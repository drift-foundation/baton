"""W116962 proposal model only. Does not replace the live inventory helpers.

Record identity includes source span, projected site, concrete label and subject.
The scanner's accepted origin/label traversal remains the input authority.
"""
import ast
from typing import NamedTuple


class Occurrence(NamedTuple):
    call: tuple
    site: str
    kind: str
    label: str
    subject: str
    lexical_label: str
    propagated: bool


def calls(b, node, origins, source_site, projected_site, *, propagated=False):
    for piece in b._scope_nodes(node):
        if not (isinstance(piece, ast.Call) and isinstance(piece.func, ast.Attribute)
                and isinstance(piece.func.value, ast.Name) and piece.func.value.id == "boundaries"
                and piece.func.attr in b.boundaries.KINDS):
            continue
        subject_at, label_at = b.POSITIONS.get(piece.func.attr, (0, 1))
        if len(piece.args) <= label_at:
            raise AssertionError(f"{source_site}:{piece.lineno} names no label")
        call = (source_site, piece.lineno, piece.col_offset, piece.end_lineno, piece.end_col_offset)
        lexical = b._label(piece.args[label_at], {})
        for context in b._contexts_at(origins, piece):
            label = b._label(piece.args[label_at], context)
            if label is None:
                raise AssertionError(f"{source_site}:{piece.lineno} names no label")
            for subject in b._origin_values(b._subject(piece.args[subject_at], context)):
                if not propagated or subject.startswith(("session:", "read:")):
                    yield Occurrence(call, projected_site, piece.func.attr, label, subject, lexical, propagated)


def occurrences(b):
    result = set()
    returns = b._helper_returns()
    for source, tree in b._sources():
        helpers = b._helpers(tree, source.name)
        for site, node in b._functions(tree, source.name):
            origins = b._origins(node, site, returns)
            result.update(calls(b, node, origins, site, site))
            for where, helper, inside in b._delegations(node, origins, helpers, site=site, returns=returns):
                result.update(calls(b, helper, inside, where, site, propagated=True))
    return frozenset(result)


def claims(b, records, entries, delegated):
    """Keep the existing subject matching and exact-before-covering precedence.

    Select the matching occurrences themselves, not every call sharing a label.
    """
    by_site = {}
    for record in records:
        by_site.setdefault(record.site, set()).add(record)
    result = {}
    for entry in entries:
        places = [(entry[1], b._claims(entry))]
        if entry in delegated:
            places.append(delegated[entry])
        for site, stem in places:
            available = by_site.get(site, ())
            selected = {r for r in available if r.subject == stem or r.subject.startswith(stem + ".")}
            if not selected and entry[0] != "injected":
                selected = {r for r in available if stem.startswith(r.subject + "[") or r.subject.startswith(stem + "[")}
            for record in selected:
                result.setdefault(record, set()).add(entry)
    return result


def account(records, claimed, exceptions):
    """Resolve declarations only through exact, actually claimed propagation.

    A lexical private parameter origin is a declaration template. Real local
    read/session origins and every propagated context retain their own duty.
    A declaration-only exemption cannot spread to another source call.
    """
    links = {}
    for record in claimed:
        if record.propagated:
            links.setdefault(record.call, set()).add(record)
    resolved, residual = {}, set()
    for record in records:
        if record in claimed or (record.site, record.kind, record.label) in exceptions:
            continue
        private = record.call[0].rsplit(".", 1)[-1].split(":")[-1].startswith("_")
        if not record.propagated and private and record.subject.startswith("caller:") and record.call in links:
            resolved[record] = links[record.call]
        else:
            residual.add(record)
    return resolved, frozenset(residual)
