#!/usr/bin/env python3
import sys, re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

from jinja2 import Environment, FileSystemLoader


class ParseError(Exception):
    def __init__(self, line: int, snippet: str):
        self.line = line
        self.snippet = snippet
        super().__init__(f"syntax error at line {line}: {snippet.strip()}")


class LanguageSpec:
    def __init__(self, name: str, template: str, pseudo_initial_state: str, pseudo_final_state: str):
        self.name = name
        self.template = template
        self.pseudo_initial_state = pseudo_initial_state
        self.pseudo_final_state = pseudo_final_state
        self.namespace_base = "statesurf"
        self.type_prefix = "StateMachine"

    def configure(self, namespace_base: str, type_prefix: str):
        self.namespace_base = namespace_base
        self.type_prefix = type_prefix

    def state_literal(self, name: str) -> str:
        raise NotImplementedError

    def event_literal(self, name: str) -> str:
        raise NotImplementedError

    def action_literal(self, name: str) -> str:
        raise NotImplementedError

    def guard_literal(self, name: str) -> str:
        raise NotImplementedError

    def default_event_literal(self) -> str:
        raise NotImplementedError

    def current_state_ref(self) -> str:
        raise NotImplementedError

    def event_param_ref(self) -> str:
        raise NotImplementedError

    def call_transition(self, src: str, dst: str, event: str) -> str:
        raise NotImplementedError

    def call_entry(self, state: str) -> str:
        raise NotImplementedError

    def call_exit(self, state: str) -> str:
        raise NotImplementedError

    def call_action(self, state: str, event: str, action: str) -> str:
        raise NotImplementedError

    def guard_condition(self, state: str, event: str, guard: str) -> str:
        raise NotImplementedError

    def set_state(self, state: str) -> str:
        raise NotImplementedError

    def set_started_false(self) -> str:
        raise NotImplementedError

    def set_terminated_true(self) -> str:
        raise NotImplementedError

    def return_statement(self) -> str:
        raise NotImplementedError

    def case_epilogue(self) -> Optional[str]:
        return None

    def guard_open(self, condition: str) -> str:
        return f"{condition}{{"

    def guard_close(self) -> Optional[str]:
        return "}"


class CppLanguageSpec(LanguageSpec):
    def __init__(self):
        super().__init__(
            name="cpp",
            template="cpp/machine.j2",
            pseudo_initial_state="InitialPseudoState",
            pseudo_final_state="FinalPseudoState",
        )
        self._callbacks_ref = "callbacks_"
        self._current_state = "s_"
        self._event_param = "e"
        self._started_var = "started_"
        self._terminated_var = "terminated_"

    def configure(self, namespace_base: str, type_prefix: str):
        super().configure(namespace_base, type_prefix)
        prefix = ''.join(part.capitalize() for part in split_camel(type_prefix).split('_') if part)
        prefix = prefix or "StateMachine"
        self._state_enum = f"{prefix}State"
        self._event_enum = f"{prefix}Event"
        self._guard_enum = f"{prefix}GuardId"
        self._action_enum = f"{prefix}ActionId"
        self._callbacks_type = f"{prefix}Callbacks"
        self._machine_type = f"{prefix}Machine"

    def state_literal(self, name: str) -> str:
        return f"{self._state_enum}::{name}"

    def event_literal(self, name: str) -> str:
        return f"{self._event_enum}::{name}"

    def action_literal(self, name: str) -> str:
        return f"{self._action_enum}::{name}"

    def guard_literal(self, name: str) -> str:
        return f"{self._guard_enum}::{name}"

    def default_event_literal(self) -> str:
        return f"{self._event_enum}{{}}"

    def current_state_ref(self) -> str:
        return self._current_state

    def event_param_ref(self) -> str:
        return self._event_param

    def call_transition(self, src: str, dst: str, event: str) -> str:
        return f"on_transition({src}, {dst}, {event});"

    def call_entry(self, state: str) -> str:
        return f"{self._callbacks_ref}.on_entry({state});"

    def call_exit(self, state: str) -> str:
        return f"{self._callbacks_ref}.on_exit({state});"

    def call_action(self, state: str, event: str, action: str) -> str:
        return f"{self._callbacks_ref}.action({state}, {event}, {action});"

    def guard_condition(self, state: str, event: str, guard: str) -> str:
        return f"if ({self._callbacks_ref}.guard({state}, {event}, {guard})) "

    def set_state(self, state: str) -> str:
        return f"{self._current_state} = {state};"

    def set_started_false(self) -> str:
        return f"{self._started_var} = false;"

    def set_terminated_true(self) -> str:
        return f"{self._terminated_var} = true;"

    def return_statement(self) -> str:
        return "return;"

    def case_epilogue(self) -> Optional[str]:
        return "return;"


class RustLanguageSpec(LanguageSpec):
    def __init__(self):
        super().__init__(
            name="rust",
            template="rust/machine.rs.j2",
            pseudo_initial_state="InitialPseudoState",
            pseudo_final_state="FinalPseudoState",
        )
        self._callbacks_ref = "self.callbacks"
        self._state_ref = "self.state"
        self._event_ref = "event"
        self._started_ref = "self.started"
        self._terminated_ref = "self.terminated"

    def configure(self, namespace_base: str, type_prefix: str):
        super().configure(namespace_base, type_prefix)
        prefix = ''.join(part.capitalize() for part in split_camel(type_prefix).split('_') if part)
        prefix = prefix or "StateMachine"
        self._state_enum = f"{prefix}State"
        self._event_enum = f"{prefix}Event"
        self._guard_enum = f"{prefix}GuardId"
        self._action_enum = f"{prefix}ActionId"
        self._callbacks_trait = f"{prefix}Callbacks"
        self._machine_type = f"{prefix}Machine"

    def state_literal(self, name: str) -> str:
        return f"{self._state_enum}::{name}"

    def event_literal(self, name: str) -> str:
        return f"{self._event_enum}::{name}"

    def action_literal(self, name: str) -> str:
        return f"{self._action_enum}::{name}"

    def guard_literal(self, name: str) -> str:
        return f"{self._guard_enum}::{name}"

    def default_event_literal(self) -> str:
        return f"{self._event_enum}::default()"

    def current_state_ref(self) -> str:
        return self._state_ref

    def event_param_ref(self) -> str:
        return self._event_ref

    def call_transition(self, src: str, dst: str, event: str) -> str:
        return f"on_transition({src}, {dst}, {event});"

    def call_entry(self, state: str) -> str:
        return f"{self._callbacks_ref}.on_entry({state});"

    def call_exit(self, state: str) -> str:
        return f"{self._callbacks_ref}.on_exit({state});"

    def call_action(self, state: str, event: str, action: str) -> str:
        return f"{self._callbacks_ref}.action({state}, {event}, {action});"

    def guard_condition(self, state: str, event: str, guard: str) -> str:
        return f"if {self._callbacks_ref}.guard({state}, {event}, {guard}) "

    def set_state(self, state: str) -> str:
        return f"{self._state_ref} = {state};"

    def set_started_false(self) -> str:
        return f"{self._started_ref} = false;"

    def set_terminated_true(self) -> str:
        return f"{self._terminated_ref} = true;"

    def return_statement(self) -> str:
        return "return;"


class PythonLanguageSpec(LanguageSpec):
    def __init__(self):
        super().__init__(
            name="python",
            template="python/machine.py.j2",
            pseudo_initial_state="InitialPseudoState",
            pseudo_final_state="FinalPseudoState",
        )
        self._callbacks_ref = "self._callbacks"
        self._state_ref = "self._state"
        self._event_ref = "event"
        self._started_ref = "self._started"
        self._terminated_ref = "self._terminated"

    def configure(self, namespace_base: str, type_prefix: str):
        super().configure(namespace_base, type_prefix)
        prefix = ''.join(part.capitalize() for part in split_camel(type_prefix).split('_') if part)
        prefix = prefix or "StateMachine"
        self._state_enum = f"{prefix}State"
        self._event_enum = f"{prefix}Event"
        self._guard_enum = f"{prefix}GuardId"
        self._action_enum = f"{prefix}ActionId"
        self._callbacks_type = f"{prefix}Callbacks"
        self._machine_type = f"{prefix}Machine"

    def state_literal(self, name: str) -> str:
        return f"{self._state_enum}.{name}"

    def event_literal(self, name: str) -> str:
        return f"{self._event_enum}.{name}"

    def action_literal(self, name: str) -> str:
        return f"{self._action_enum}.{name}"

    def guard_literal(self, name: str) -> str:
        return f"{self._guard_enum}.{name}"

    def default_event_literal(self) -> str:
        return "self._default_event()"

    def current_state_ref(self) -> str:
        return self._state_ref

    def event_param_ref(self) -> str:
        return self._event_ref

    def call_transition(self, src: str, dst: str, event: str) -> str:
        return f"on_transition({src}, {dst}, {event})"

    def call_entry(self, state: str) -> str:
        return f"{self._callbacks_ref}.on_entry({state})"

    def call_exit(self, state: str) -> str:
        return f"{self._callbacks_ref}.on_exit({state})"

    def call_action(self, state: str, event: str, action: str) -> str:
        return f"{self._callbacks_ref}.action({state}, {event}, {action})"

    def guard_condition(self, state: str, event: str, guard: str) -> str:
        return f"if {self._callbacks_ref}.guard({state}, {event}, {guard})"

    def guard_open(self, condition: str) -> str:
        return f"{condition}:"

    def guard_close(self) -> Optional[str]:
        return None

    def set_state(self, state: str) -> str:
        return f"{self._state_ref} = {state}"

    def set_started_false(self) -> str:
        return f"{self._started_ref} = False"

    def set_terminated_true(self) -> str:
        return f"{self._terminated_ref} = True"

    def return_statement(self) -> str:
        return "return"

    def case_epilogue(self) -> Optional[str]:
        return "return"


LANGUAGE_SPECS = {
    "cpp": CppLanguageSpec(),
    "rust": RustLanguageSpec(),
    "python": PythonLanguageSpec(),
}

class Node:
    def __init__(self, name: str, parent: Optional['Node']):
        self.name = name
        self.parent = parent
        self.children: Dict[str, Node] = {}
        self.initial_target: Optional[str] = None
        self.initial_action: Optional[str] = None
        self.entry_actions: List[str] = []
        self.exit_actions: List[str] = []

class Transition:
    def __init__(self, src: str, dst: Optional[str], event: Optional[str],
                 guard: Optional[str], action: Optional[str], internal: bool=False):
        self.src = src
        self.dst = dst  # None for final [*]
        self.event = event
        self.guard = guard
        self.action = action
        self.internal = internal

class Model:
    def __init__(self):
        self.root = Node("__root__", None)
        self.nodes: Dict[str, Node] = {"__root__": self.root}
        self.transitions: List[Transition] = []
        self.events: Set[str] = set()
        self.guards: Set[str] = set()
        self.actions: Set[str] = set()

    def ensure_node(self, name: str, parent: Node) -> Node:
        if name in self.nodes:
            n = self.nodes[name]
            if n.parent is None:
                n.parent = parent
            if n.parent is parent:
                parent.children[name] = n
            return n
        n = Node(name, parent)
        self.nodes[name] = n
        parent.children[name] = n
        return n

    def ancestors(self, name: str) -> List[Node]:
        res=[]
        n=self.nodes[name]
        while n is not None and n.name!="__root__":
            res.append(n)
            n=n.parent
        return res  # leaf.. up

    def lca(self, a: str, b: str) -> Optional[Node]:
        aa = self.ancestors(a)
        bb = self.ancestors(b)
        aset = {n.name for n in aa}
        for n in bb:
            if n.name in aset:
                return n
        return None

    def is_composite(self, name: str) -> bool:
        return len(self.nodes[name].children)>0

    def initial_leaf(self, name: str) -> str:
        n = self.nodes[name]
        while n.children:
            if n.initial_target:
                t = self.nodes[n.initial_target]
            else:
                # first child by name
                t = list(n.children.values())[0]
            n = t
        return n.name

def parse_puml(path: Path) -> Model:
    text = path.read_text(encoding="utf-8")
    m = Model()
    stack: List[Node] = [m.root]

    re_state_open = re.compile(r'^\s*state\s+([A-Za-z_]\w*)\s*\{\s*$')
    re_state_decl = re.compile(r'^\s*state\s+([A-Za-z_]\w*)\s*$')
    re_close = re.compile(r'^\s*\}\s*$')
    re_initial = re.compile(r'^\s*\[\*\]\s*[-]{1,2}>\s*([A-Za-z_]\w*)\s*(?::\s*(?:([A-Za-z_]\w*)\s*)?(?:\[([A-Za-z_]\w*)\])?\s*(?:/\s*([A-Za-z_]\w*))?)?\s*$')
    re_entryexit = re.compile(r'^\s*([A-Za-z_]\w*)\s*:\s*(entry|exit)(?:\s*/\s*([A-Za-z_]\w*))?\s*$')
    re_transition = re.compile(r'^\s*([A-Za-z_]\w*)\s*[-]{1,2}>\s*([A-Za-z_\*\]\[]\w*|\[\*\])\s*:\s*([A-Za-z_]\w*)?(?:\s*\[([A-Za-z_]\w*)\])?(?:\s*/\s*([A-Za-z_]\w*)?)?\s*$')
    re_internal = re.compile(r'^\s*([A-Za-z_]\w*)\s*:\s*([A-Za-z_]\w*)?(?:\s*\[([A-Za-z_]\w*)\])?(?:\s*/\s*([A-Za-z_]\w*)?)?\s*$')

    last_line_no = 0
    for lineno, raw in enumerate(text.splitlines(), 1):
        last_line_no = lineno
        line = raw.strip()
        if not line or line.startswith("'") or line.startswith("@"):
            continue

        matched = False

        mo = re_state_open.match(line)
        if mo:
            name = mo.group(1)
            parent = stack[-1]
            node = m.ensure_node(name, parent)
            stack.append(node)
            matched = True
            continue

        mo = re_state_decl.match(line)
        if mo:
            name = mo.group(1)
            parent = stack[-1]
            m.ensure_node(name, parent)
            matched = True
            continue

        if re_close.match(line):
            if len(stack) <= 1:
                raise ParseError(lineno, raw)
            stack.pop()
            matched = True
            continue

        mo = re_initial.match(line)
        if mo:
            tgt = mo.group(1)
            action = mo.group(4)
            scope = stack[-1]
            m.ensure_node(tgt, scope)  # ensure exists
            scope.initial_target = tgt
            if action:
                scope.initial_action = action
                m.actions.add(action)
            matched = True
            continue

        mo = re_entryexit.match(line)
        if mo:
            st = mo.group(1); kind = mo.group(2); act = mo.group(3)
            m.ensure_node(st, stack[-1])
            node = m.nodes[st]
            if kind == 'entry':
                if act: node.entry_actions.append(act); m.actions.add(act)
            else:
                if act: node.exit_actions.append(act); m.actions.add(act)
            matched = True
            continue

        mo = re_transition.match(line)
        if mo:
            src, dst, ev, gd, ac = mo.groups()
            if ac == "":
                ac = None
            m.ensure_node(src, stack[-1])
            dst_name = None if dst=="[*]" else dst
            if dst_name:
                # ensure known (attach to nearest scope if unknown)
                if dst_name not in m.nodes:
                    m.ensure_node(dst_name, stack[-1])
            if ev: m.events.add(ev)
            if gd: m.guards.add(gd)
            if ac: m.actions.add(ac)
            m.transitions.append(Transition(src, dst_name, ev, gd, ac, internal=False))
            matched = True
            continue

        mo = re_internal.match(line)
        if mo:
            matched = True
            st, ev, gd, ac = mo.groups()
            if ac == "":
                ac = None
            if ev in ('entry','exit'):
                if gd or ac or '/' in line:
                    raise ParseError(lineno, raw)
                continue
            m.ensure_node(st, stack[-1])
            if ev: m.events.add(ev)
            if gd: m.guards.add(gd)
            if ac: m.actions.add(ac)
            m.transitions.append(Transition(st, st, ev, gd, ac, internal=True))
            continue

        if not matched:
            raise ParseError(lineno, raw)

    if len(stack) > 1:
        raise ParseError(last_line_no, "missing } before end of file")

    return m

def topo_states(m: Model) -> List[str]:
    order = []
    def walk(n: Node):
        for child in n.children.values():
            order.append(child.name)
            walk(child)
    walk(m.root)
    return order

def compute_state_depth(m: Model, name: str) -> int:
    d=0; n=m.nodes[name]
    while n.parent and n.parent.name!="__root__":
        d+=1; n=n.parent
    return d

def build_transitions_by_state(m: Model):
    by_src = {}
    for t in m.transitions:
        by_src.setdefault(t.src, []).append(t)
    result = {}
    for s in m.nodes:
        if s == "__root__": continue
        cand = []
        n = m.nodes[s]
        while n and n.name != "__root__":
            cand.extend(by_src.get(n.name, []))
            n = n.parent
        evmap = {}
        for t in cand:
            if t.event is None: continue
            evmap.setdefault(t.event, []).append(t)
        for e, lst in evmap.items():
            lst.sort(key=lambda t: compute_state_depth(m, t.src), reverse=True)
        result[s] = evmap
    return result

def normalize_identifier(name: str) -> str:
    return re.sub(r'[^A-Za-z0-9_]', '_', name)


def split_camel(name: str) -> str:
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)


def generate_namespace_base(puml_path: Path) -> str:
    base = puml_path.stem
    base = split_camel(base)
    base = normalize_identifier(base)
    base = base.strip('_') or "state_machine"
    return base.lower()


def generate_type_prefix(puml_path: Path) -> str:
    base = puml_path.stem
    base = normalize_identifier(split_camel(base))
    parts = [part for part in base.split('_') if part]
    return ''.join(part.capitalize() for part in parts) or "StateMachine"


def gen_code(m, machine_name: str, language: str, namespace_base: str, type_prefix: str) -> str:
    namespace_base = normalize_identifier(namespace_base).lower() or "state_machine"
    type_prefix = type_prefix or "StateMachine"
    type_prefix = ''.join(part.capitalize() for part in split_camel(type_prefix).split('_') if part)
    type_prefix = type_prefix or "StateMachine"
    if language not in LANGUAGE_SPECS:
        raise ValueError(
            f"Unsupported language '{language}'. Available: {', '.join(sorted(LANGUAGE_SPECS.keys()))}"
        )
    spec = LANGUAGE_SPECS[language]
    spec.configure(namespace_base, type_prefix)

    def sanitize_id(x: str) -> str:
        return re.sub(r'[^A-Za-z0-9_]', '_', x)

    states = [s for s in topo_states(m) if s != "__root__"]
    events = sorted(m.events, key=lambda x: x)

    guard_ids: List[str] = []
    guard_map: Dict[str, str] = {}
    action_ids: List[str] = []
    action_map: Dict[str, str] = {}

    def normalized_id(name: str) -> str:
        sid = sanitize_id(name)
        if not sid:
            sid = "_"
        if sid[0].isdigit():
            sid = "_" + sid
        return sid

    def register_guard(name: str) -> str:
        gid = normalized_id(name)
        if gid not in guard_ids:
            guard_ids.append(gid)
        guard_map[name] = gid
        return gid

    def register_action(name: str) -> str:
        aid = normalized_id(name)
        if aid not in action_ids:
            action_ids.append(aid)
        action_map[name] = aid
        return aid

    for t in m.transitions:
        if t.guard:
            register_guard(t.guard)
        if t.action:
            register_action(t.action)

    for st, node in m.nodes.items():
        if st == "__root__":
            continue
        for a in node.entry_actions:
            register_action(a)
        for a in node.exit_actions:
            register_action(a)

    def collect_initial_actions(n: Node):
        if n.initial_action:
            register_action(n.initial_action)
        for c in n.children.values():
            collect_initial_actions(c)

    collect_initial_actions(m.root)

    by_state = build_transitions_by_state(m)

    state_ids_map = {name: sanitize_id(name) for name in states}
    event_ids_map = {name: sanitize_id(name) for name in events}

    def indent(level: int, text: str) -> str:
        return "  " * level + text

    def emit_exit_chain_for_state(sname: str) -> List[str]:
        lines: List[str] = []
        n = m.nodes[sname]
        while n and n.name != "__root__":
            node_id = state_ids_map[n.name]
            for act in n.exit_actions:
                aid = action_map[act]
                lines.append(
                    spec.call_action(
                        spec.state_literal(node_id),
                        spec.event_param_ref(),
                        spec.action_literal(aid),
                    )
                )
            lines.append(spec.call_exit(spec.state_literal(node_id)))
            n = n.parent
        return lines

    def append_state(lst: List[str], name: str):
        if name != "__root__":
            if not lst or lst[-1] != name:
                lst.append(name)

    def entry_chain_nodes(from_lca_name: str, dest_leaf: str) -> List[str]:
        acc: List[str] = []
        n = m.nodes[dest_leaf]
        while n and n.name != from_lca_name:
            if n.name != "__root__":
                acc.append(n.name)
            n = n.parent
        acc.reverse()
        return acc

    start_lines: List[str] = []
    start_target_state: Optional[str] = None

    root_init = m.root.initial_target
    if root_init is None and states:
        root_init = states[0]
    if root_init:
        leaf = m.initial_leaf(root_init)
        start_target_state = state_ids_map[leaf]
        path: List[Node] = []
        n = m.nodes[leaf]
        while n and n.name != "__root__":
            path.append(n)
            n = n.parent
        path_nodes = list(reversed(path))
        first_child: Dict[str, str] = {}
        for node in path_nodes:
            parent = node.parent
            if parent and parent.name not in first_child:
                first_child[parent.name] = node.name
        for node in path_nodes:
            parent = node.parent
            if parent:
                initial_action = parent.initial_action
                if initial_action and first_child.get(parent.name) == node.name:
                    aid = action_map[initial_action]
                    action_state = node.name if parent.name == "__root__" else parent.name
                    start_lines.append(
                        spec.call_action(
                            spec.state_literal(state_ids_map[action_state]),
                            spec.default_event_literal(),
                            spec.action_literal(aid),
                        )
                    )
            start_lines.append(spec.call_entry(spec.state_literal(state_ids_map[node.name])))
            for act in node.entry_actions:
                aid = action_map[act]
                start_lines.append(
                    spec.call_action(
                        spec.state_literal(state_ids_map[node.name]),
                        spec.default_event_literal(),
                        spec.action_literal(aid),
                    )
                )

    reset_lines: List[str] = [
        spec.set_started_false(),
        spec.set_state(spec.state_literal(spec.pseudo_initial_state)),
    ]

    default_event_variant = event_ids_map[events[0]] if events else None
    pseudo_initial_literal = spec.state_literal(spec.pseudo_initial_state)
    pseudo_final_literal = spec.state_literal(spec.pseudo_final_state)

    start_transition_line: Optional[str] = None
    start_state_line: Optional[str] = None
    fallback_lines: List[str] = []

    if start_target_state:
        target_literal = spec.state_literal(start_target_state)
        start_transition_line = spec.call_transition(
            pseudo_initial_literal,
            target_literal,
            spec.default_event_literal(),
        )
        start_state_line = spec.set_state(target_literal)
    else:
        fallback_lines = [
            spec.call_transition(
                pseudo_initial_literal,
                pseudo_final_literal,
                spec.default_event_literal(),
            ),
            spec.call_entry(pseudo_final_literal),
            spec.set_state(pseudo_final_literal),
            spec.set_terminated_true(),
        ]

    state_cases: List[Dict[str, object]] = []

    for s in states:
        case_label = spec.state_literal(state_ids_map[s])
        evmap = by_state.get(s, {})
        event_blocks: List[Dict[str, object]] = []
        for ev, transitions in evmap.items():
            event_label = spec.event_literal(event_ids_map[ev])
            body_lines: List[str] = []
            stop_after_transition = False
            emit_case_epilogue = True
            for t in transitions:
                if stop_after_transition:
                    break
                if t.internal:
                    cond = ""
                    if t.guard:
                        gid = guard_map[t.guard]
                        cond = spec.guard_condition(
                            spec.current_state_ref(),
                            spec.event_param_ref(),
                            spec.guard_literal(gid),
                        )
                        guard_open = spec.guard_open(cond)
                        if guard_open:
                            body_lines.append(indent(6, guard_open))
                        inner_indent = 7
                    else:
                        inner_indent = 6
                    body_lines.append(
                        indent(
                            inner_indent,
                            spec.call_transition(
                                spec.current_state_ref(),
                                spec.current_state_ref(),
                                spec.event_param_ref(),
                            ),
                        )
                    )
                    if t.action:
                        aid = action_map[t.action]
                        body_lines.append(
                            indent(
                                inner_indent,
                                spec.call_action(
                                    spec.current_state_ref(),
                                    spec.event_param_ref(),
                                    spec.action_literal(aid),
                                ),
                            )
                        )
                    body_lines.append(indent(inner_indent, spec.return_statement()))
                    if t.guard:
                        guard_close = spec.guard_close()
                        if guard_close:
                            body_lines.append(indent(6, guard_close))
                    else:
                        stop_after_transition = True
                        emit_case_epilogue = False
                    continue

                if t.dst is None:
                    cond = ""
                    if t.guard:
                        gid = guard_map[t.guard]
                        cond = spec.guard_condition(
                            spec.current_state_ref(),
                            spec.event_param_ref(),
                            spec.guard_literal(gid),
                        )
                    if t.guard:
                        guard_open = spec.guard_open(cond)
                        if guard_open:
                            body_lines.append(indent(6, guard_open))
                        inner_indent = 7
                    else:
                        inner_indent = 6
                    body_lines.append(
                        indent(
                            inner_indent,
                            spec.call_transition(
                                spec.current_state_ref(),
                                pseudo_final_literal,
                                spec.event_param_ref(),
                            ),
                        )
                    )
                    for ln in emit_exit_chain_for_state(s):
                        body_lines.append(indent(inner_indent, ln))
                    if t.action:
                        aid = action_map[t.action]
                        body_lines.append(
                            indent(
                                inner_indent,
                                spec.call_action(
                                    spec.current_state_ref(),
                                    spec.event_param_ref(),
                                    spec.action_literal(aid),
                                ),
                            )
                        )
                    body_lines.append(indent(inner_indent, spec.call_entry(pseudo_final_literal)))
                    body_lines.append(indent(inner_indent, spec.set_state(pseudo_final_literal)))
                    body_lines.append(indent(inner_indent, spec.set_terminated_true()))
                    body_lines.append(indent(inner_indent, spec.return_statement()))
                    if t.guard:
                        guard_close = spec.guard_close()
                        if guard_close:
                            body_lines.append(indent(6, guard_close))
                    else:
                        stop_after_transition = True
                        emit_case_epilogue = False
                    continue

                dest_leaf = m.initial_leaf(t.dst) if m.is_composite(t.dst) else t.dst
                exit_nodes: List[str] = []
                n = m.nodes[s]
                source_node = m.nodes.get(t.src)
                if not t.internal and source_node is not None and source_node.name == s:
                    append_state(exit_nodes, s)
                    n = n.parent
                else:
                    while n and (source_node is None or n.name != source_node.name):
                        append_state(exit_nodes, n.name)
                        n = n.parent
                dest_within_source = False
                target_node = m.nodes.get(t.dst) if t.dst is not None else None
                target_is_ancestor = False
                if t.src in m.nodes:
                    dn = m.nodes[dest_leaf]
                    while dn:
                        if dn.name == t.src:
                            dest_within_source = True
                            break
                        dn = dn.parent
                if target_node is not None and source_node is not None:
                    anc = source_node
                    while anc and anc.name != "__root__":
                        if anc.name == target_node.name:
                            target_is_ancestor = True
                            break
                        anc = anc.parent
                if not dest_within_source and source_node is not None and source_node.name != "__root__":
                    append_state(exit_nodes, t.src)
                    n = source_node.parent
                else:
                    n = source_node.parent if source_node is not None else n
                lca_src_dest = m.lca(t.src, dest_leaf) if t.src in m.nodes else None
                if not dest_within_source:
                    while n and (lca_src_dest is None or n.name != lca_src_dest.name):
                        append_state(exit_nodes, n.name)
                        n = n.parent
                if target_is_ancestor and target_node is not None and t.src != s:
                    current_node = m.nodes[s]
                    anc = current_node.parent
                    while anc and anc.name != "__root__":
                        if anc.name == target_node.name:
                            break
                        append_state(exit_nodes, anc.name)
                        anc = anc.parent
                exit_common = False
                if (not t.internal) and dest_within_source and t.src == t.dst:
                    exit_common = True
                if dest_within_source and source_node is not None:
                    if target_is_ancestor and target_node is not None:
                        entry_anchor_name = target_node.name
                    else:
                        entry_anchor_name = t.src
                else:
                    lca_node = lca_src_dest if lca_src_dest is not None else (source_node if source_node is not None else None)
                    entry_anchor_name = lca_node.name if lca_node is not None else "__root__"
                entry_nodes = entry_chain_nodes(entry_anchor_name, dest_leaf)
                if exit_common and source_node is not None and source_node.name != s:
                    append_state(exit_nodes, source_node.name)
                cond = ""
                if t.guard:
                    gid = guard_map[t.guard]
                    cond = spec.guard_condition(
                        spec.current_state_ref(),
                        spec.event_param_ref(),
                        spec.guard_literal(gid),
                    )
                if t.guard:
                    guard_open = spec.guard_open(cond)
                    if guard_open:
                        body_lines.append(indent(6, guard_open))
                    inner_indent = 7
                else:
                    inner_indent = 6
                body_lines.append(
                    indent(
                        inner_indent,
                        spec.call_transition(
                            spec.current_state_ref(),
                            spec.state_literal(state_ids_map[dest_leaf]),
                            spec.event_param_ref(),
                        ),
                    )
                )
                for en in exit_nodes:
                    node = m.nodes[en]
                    node_id = state_ids_map[node.name]
                    for act in node.exit_actions:
                        aid = action_map[act]
                        body_lines.append(
                            indent(
                                inner_indent,
                                spec.call_action(
                                    spec.state_literal(node_id),
                                    spec.event_param_ref(),
                                    spec.action_literal(aid),
                                ),
                            )
                        )
                    body_lines.append(indent(inner_indent, spec.call_exit(spec.state_literal(node_id))))
                if t.action:
                    aid = action_map[t.action]
                    body_lines.append(
                        indent(
                            inner_indent,
                            spec.call_action(
                                spec.current_state_ref(),
                                spec.event_param_ref(),
                                spec.action_literal(aid),
                            ),
                        )
                    )
                if exit_common and source_node is not None and source_node.name != "__root__":
                    source_id = state_ids_map[source_node.name]
                    body_lines.append(indent(inner_indent, spec.call_entry(spec.state_literal(source_id))))
                    for act in source_node.entry_actions:
                        aid = action_map[act]
                        body_lines.append(
                            indent(
                                inner_indent,
                                spec.call_action(
                                    spec.state_literal(source_id),
                                    spec.event_param_ref(),
                                    spec.action_literal(aid),
                                ),
                            )
                        )
                for en in entry_nodes:
                    node = m.nodes[en]
                    node_id = state_ids_map[node.name]
                    body_lines.append(indent(inner_indent, spec.call_entry(spec.state_literal(node_id))))
                    for act in node.entry_actions:
                        aid = action_map[act]
                        body_lines.append(
                            indent(
                                inner_indent,
                                spec.call_action(
                                    spec.state_literal(node_id),
                                    spec.event_param_ref(),
                                    spec.action_literal(aid),
                                ),
                            )
                        )
                body_lines.append(indent(inner_indent, spec.set_state(spec.state_literal(state_ids_map[dest_leaf]))))
                body_lines.append(indent(inner_indent, spec.return_statement()))
                if t.guard:
                    guard_close = spec.guard_close()
                    if guard_close:
                        body_lines.append(indent(6, guard_close))
                else:
                    stop_after_transition = True
                    emit_case_epilogue = False
            epilogue = spec.case_epilogue()
            if emit_case_epilogue and epilogue:
                body_lines.append(indent(6, epilogue))
            event_blocks.append(
                {
                    "enum_name": event_ids_map[ev],
                    "case_label": event_label,
                    "lines": body_lines,
                }
            )
        state_cases.append(
            {
                "enum_name": state_ids_map[s],
                "case_label": case_label,
                "events": event_blocks,
            }
        )

    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)), trim_blocks=True, lstrip_blocks=True)
    template = env.get_template(spec.template)

    code = template.render(
        machine_name=machine_name,
        namespace_base=namespace_base,
        type_prefix=type_prefix,
        states=[state_ids_map[s] for s in states] or ["__None"],
        events=[event_ids_map[e] for e in events] or ["__None"],
        guard_ids=guard_ids if guard_ids else ["__None"],
        action_ids=action_ids if action_ids else ["__None"],
        reset_lines=reset_lines,
        state_cases=state_cases,
        start_lines=start_lines,
        has_start_target=start_target_state is not None,
        start_transition_line=start_transition_line,
        start_state_line=start_state_line,
        fallback_lines=fallback_lines,
        pseudo_initial=spec.pseudo_initial_state,
        pseudo_final=spec.pseudo_final_state,
        pseudo_initial_literal=pseudo_initial_literal,
        pseudo_final_literal=pseudo_final_literal,
        current_state_ref=spec.current_state_ref(),
        event_param_ref=spec.event_param_ref(),
        default_event_variant=default_event_variant,
        default_event_literal=spec.default_event_literal(),
        return_statement=spec.return_statement(),
    )
    return code


def generate_python_assets(
    model: Model,
    machine_name: str,
    namespace_base: str,
    type_prefix: str,
    output_path: Path,
) -> None:
    code = gen_code(model, machine_name, "python", namespace_base, type_prefix)
    output_path.write_text(code, encoding="utf-8")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def render_template(template_name: str, **context) -> str:
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)), trim_blocks=True, lstrip_blocks=True)
    template = env.get_template(template_name)
    return template.render(**context)


def generate(
    input_path: Path,
    output_path: Path,
    machine_name: Optional[str] = None,
    language: str = "cpp",
) -> None:
    model = parse_puml(input_path)
    namespace_base = generate_namespace_base(input_path)
    type_prefix = generate_type_prefix(input_path)
    effective_machine_name = machine_name or f"{type_prefix}Machine"
    code = gen_code(model, effective_machine_name, language, namespace_base, type_prefix)
    output_path.write_text(code, encoding="utf-8")

def simulate(
    input_path: Path,
    simulation_dir: Path,
    machine_name: Optional[str] = None,
    plantuml_cmd: str = "plantuml",
) -> None:
    model = parse_puml(input_path)
    namespace_base = generate_namespace_base(input_path)
    type_prefix = generate_type_prefix(input_path)
    effective_machine_name = machine_name or f"{type_prefix}Machine"

    ensure_dir(simulation_dir)

    machine_module_path = simulation_dir / "machine.py"
    generate_python_assets(model, effective_machine_name, namespace_base, type_prefix, machine_module_path)

    original_puml_copy = simulation_dir / input_path.name
    original_text = input_path.read_text(encoding="utf-8")
    original_puml_copy.write_text(original_text, encoding="utf-8")

    def sanitize(name: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9_]", "_", name)
        if not cleaned:
            cleaned = "_"
        if cleaned[0].isdigit():
            cleaned = "_" + cleaned
        return cleaned

    event_names = [sanitize(ev) for ev in sorted(model.events)]

    module_alias = f"statesurf_sim_{sanitize(type_prefix).lower()}"

    simulator_code = render_template(
        "python/simulator_app.py.j2",
        machine_module="machine",
        machine_module_alias=module_alias,
        machine_module_filename="machine.py",
        type_prefix=type_prefix,
        machine_name=effective_machine_name,
        event_names=event_names,
        puml_filename=input_path.name,
        plantuml_cmd=plantuml_cmd,
    )
    simulator_path = simulation_dir / "simulator.py"
    simulator_path.write_text(simulator_code, encoding="utf-8")


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(description="StateSurf minimal generator (v1 subset)")
    sub = ap.add_subparsers(dest="cmd")

    g = sub.add_parser("generate")
    g.add_argument("-i", "--input", required=True)
    g.add_argument("-o", "--output", required=True)
    g.add_argument(
        "-n",
        "--name",
        default=None,
        help="Optional machine class name (defaults to <puml_file_name>Machine)",
    )
    g.add_argument("-l", "--language", default="cpp")

    s = sub.add_parser("simulate")
    s.add_argument("-i", "--input", required=True)
    s.add_argument("--sim-dir", required=True, help="Directory that will hold simulator assets")
    s.add_argument(
        "-n",
        "--name",
        default=None,
        help="Optional machine class name (defaults to <puml_file_name>Machine)",
    )
    s.add_argument(
        "--plantuml",
        default="plantuml",
        help="Path to the PlantUML CLI executable (defaults to 'plantuml')",
    )

    v = sub.add_parser("validate")
    v.add_argument("-i", "--input", required=True)

    args = ap.parse_args(argv)
    try:
        if args.cmd == "generate":
            generate(Path(args.input), Path(args.output), args.name, args.language.lower())
            return 0
        elif args.cmd == "simulate":
            simulate(
                Path(args.input),
                Path(args.sim_dir),
                machine_name=args.name,
                plantuml_cmd=args.plantuml,
            )
            print("Simulator assets generated.")
            return 0
        elif args.cmd == "validate":
            parse_puml(Path(args.input))
            print("OK")
            return 0
        else:
            ap.print_help()
            return 1
    except ParseError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))
