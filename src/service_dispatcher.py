import asyncio
from asyncio import Task
from typing import Optional

import networkx as nx

import config
from data_models import custom_exceptions as ce
from data_models.api_models import APISubmission
from data_models.internal_models import RequestEndpointType
from data_models.internal_models import ServiceOutputBase
from services.service_util import ServiceBase

ROOT_NODE = 'root'


def recursive_dep_solver(g, service: ServiceBase):
    # Recursively resolve the dependencies of the given service
    g.add_node(service)
    deps = service.dependencies()
    # If service has no deps, root is the implicit dependency
    if not deps or len(deps) == 0:
        g.add_edge(ROOT_NODE, service)
    else:
        g.add_nodes_from(deps)
        for d in deps:
            g.add_edge(d, service)
            recursive_dep_solver(g, d)


async def resolve_dependencies_and_dispatch(payload: APISubmission):
    # Resolve order by building a dependency graph
    g = nx.DiGraph()
    g.add_node(ROOT_NODE)
    for service in payload.services_as_class():
        recursive_dep_solver(g, service)

    # Walk the graph from the root
    nodes_to_visit: set[ServiceBase] = set(g.neighbors(ROOT_NODE))
    service_results: dict[ServiceBase, ServiceOutputBase] = {}
    while nodes_to_visit:
        to_raise: Optional[Exception] = None
        tasks: dict[ServiceBase, Task] = {}
        try:
            async with asyncio.TaskGroup() as tg:
                for node in nodes_to_visit:
                    # Create service specific input and provide the results of prior services
                    coro = node.inference(payload.to_service_input(node), service_results)
                    tasks[node] = tg.create_task(coro)
        except* ce.CustomExceptionBase as eg:
            # ExceptionGroups are horrible, just save first exception to report to caller
            to_raise = eg.exceptions[0]
        except* Exception as e:
            # This will cause a generic error, which is handled later
            raise e
        finally:
            # Raise any saved exceptions from the exception group above
            if to_raise:
                raise to_raise
        nodes_to_visit.clear()

        # Unpack task result
        for node, node_task in tasks.items():
            service_results[node] = node_task.result()
            for neighbor_node in g.neighbors(node):
                # Check if already visited and if dependencies are satisfied
                if neighbor_node not in service_results and neighbor_node.deps_satisfied(service_results):
                    nodes_to_visit.add(neighbor_node)

    # Parse service responses to API output
    output = {}
    for service_class, service_output in service_results.items():
        # Only return what was requested
        if service_class in payload.services_as_class():
            output[service_class.api_name()] = service_output.api_result
    return output


async def dispatch(payload: APISubmission, received_from: RequestEndpointType):
    # This is the overall timeout, there is also a per-service timeout
    effective_overall_timeout = config.calc_overall_timeout(received_from)
    try:
        async with asyncio.timeout(effective_overall_timeout):
            return await resolve_dependencies_and_dispatch(payload)
    except TimeoutError:
        raise ce.GenericTimeoutError(effective_overall_timeout)
