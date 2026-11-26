"""Authority binding of one selected MANUAL research phase."""
from baton_v12.authority import Refusal
from baton_v12.job_manager import manual, research
from tools.bootstrap import ROUTES
from tools.fresh_attempt_ports import ASSIGNMENT_CONTRACT


def _work_binding(authority, execution, descriptor):
    if descriptor["work_id"] != manual.generated_work_id(authority.authority_uuid, execution):
        raise research.refusal("generated research Work identity differs from the selected execution")
    return "manual-research.create:" + execution, "scope:" + execution


def verify_generated_phase_work(authority, execution_job_id, descriptor):

    operation, scope = _work_binding(authority, execution_job_id, descriptor)
    created = authority.work_creation(descriptor["work_id"])
    if not created or created["operation_id"] != operation or created["scope"] != scope:
        raise research.refusal("generated research Work lacks the phase creation receipt")
    work = authority.project_work(descriptor["work_id"])
    if (work["status"] != "open" or work["contract"] != ASSIGNMENT_CONTRACT or
            work["scope"] != scope or work["route"] != ROUTES["research"]):
        raise research.refusal("generated research Work no longer has its selected contract, scope and route")
    return work


def ensure_phase_work(authority, execution_job_id, descriptor, workers):
    """Materialize selected phase Work using the installed research route."""

    work_id = descriptor["work_id"]
    route = ROUTES["research"]
    try:
        if descriptor.get("work_origin") == "generated":
            operation, scope = _work_binding(authority, execution_job_id, descriptor)
            if not any(authority.handles_route(route, worker["deployment"]["participant"]) for worker in workers):
                raise research.refusal("no matching research worker handles the configured research route")
            authority.create_work(work_id, route, operation_id=operation, contract=ASSIGNMENT_CONTRACT, scope=scope)
            return verify_generated_phase_work(authority, execution_job_id, descriptor)
        work = authority.project_work(work_id)
        if work["status"] != "open" or work["contract"] != ASSIGNMENT_CONTRACT:
            raise research.refusal("research requires an open assignment-capable Work")
        if not any(authority.handles_route(work["route"], worker["deployment"]["participant"]) for worker in workers):
            raise research.refusal("no matching research worker handles the selected Work route")
        return work
    except Refusal as exc:
        raise research.refusal("research Work authorization refused: " + str(exc)) from exc
