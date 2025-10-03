#!/usr/bin/env python3
import sys, re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

from jinja2 import Environment, FileSystemLoader

PSEUDO_INITIAL_STATE = "InitialPseudoState"
PSEUDO_FINAL_STATE = "FinalPseudoState"

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
    re_initial = re.compile(r'^\s*\[\*\]\s*[-]{1,2}>\s*([A-Za-z_]\w*)\s*(?::\s*(?:([A-Za-z_]\w*)\s*)?(?:\[(.*?)\])?\s*(?:/\s*([A-Za-z_]\w*))?)?\s*$')
    re_entryexit = re.compile(r'^\s*([A-Za-z_]\w*)\s*:\s*(entry|exit)(?:\s*/\s*([A-Za-z_]\w*))?\s*$')
    re_transition = re.compile(r'^\s*([A-Za-z_]\w*)\s*[-]{1,2}>\s*([A-Za-z_\*\]\[]\w*|\[\*\])\s*:\s*([A-Za-z_]\w*)?(?:\s*\[([^\]]+)\])?(?:\s*/\s*([A-Za-z_]\w*)?)?\s*$')
    re_internal = re.compile(r'^\s*([A-Za-z_]\w*)\s*:\s*([A-Za-z_]\w*)?(?:\s*\[([^\]]+)\])?(?:\s*/\s*([A-Za-z_]\w*)?)?\s*$')

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("'") or line.startswith("@"):
            continue

        mo = re_state_open.match(line)
        if mo:
            name = mo.group(1)
            parent = stack[-1]
            node = m.ensure_node(name, parent)
            stack.append(node)
            continue

        mo = re_state_decl.match(line)
        if mo:
            name = mo.group(1)
            parent = stack[-1]
            m.ensure_node(name, parent)
            continue

        if re_close.match(line):
            if len(stack)>1:
                stack.pop()
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
            continue

        mo = re_internal.match(line)
        if mo:
            st, ev, gd, ac = mo.groups()
            if ev in ('entry','exit'):
                continue
            if ac == "":
                ac = None
            m.ensure_node(st, stack[-1])
            if ev: m.events.add(ev)
            if gd: m.guards.add(gd)
            if ac: m.actions.add(ac)
            m.transitions.append(Transition(st, st, ev, gd, ac, internal=True))
            continue

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

def gen_header(m, machine_name: str) -> str:
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
                lines.append("impl_.action(State::{}, e, ActionId::{});".format(node_id, aid))
            lines.append("impl_.on_exit(State::{});".format(node_id))
            n = n.parent
        return lines

    def append_state(lst: List[str], name: str):
        if name != "__root__":
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
                    start_lines.append("impl_.action(State::{}, Event{{}}, ActionId::{});".format(state_ids_map[action_state], aid))
            start_lines.append("impl_.on_entry(State::{});".format(state_ids_map[node.name]))
            for act in node.entry_actions:
                aid = action_map[act]
                start_lines.append("impl_.action(State::{}, Event{{}}, ActionId::{});".format(state_ids_map[node.name], aid))

    reset_lines: List[str] = [
        "started_ = false;",
        "s_ = State::{};".format(PSEUDO_INITIAL_STATE)
    ]

    state_cases: List[Dict[str, object]] = []

    for s in states:
        evmap = by_state.get(s, {})
        event_blocks: List[Dict[str, object]] = []
        for ev, transitions in evmap.items():
            body_lines: List[str] = []
            for t in transitions:
                if t.internal:
                    cond = ""
                    if t.guard:
                        gid = guard_map[t.guard]
                        cond = "if (impl_.guard(s_, e, GuardId::{})) ".format(gid)
                    body_lines.append(indent(6, "{}{{".format(cond) if cond else "{"))
                    body_lines.append(indent(7, "on_transition(s_, s_, e);"))
                    if t.action:
                        aid = action_map[t.action]
                        body_lines.append(indent(7, "impl_.action(s_, e, ActionId::{});".format(aid)))
                    body_lines.append(indent(7, "return;"))
                    body_lines.append(indent(6, "}"))
                    continue

                if t.dst is None:
                    cond = ""
                    if t.guard:
                        gid = guard_map[t.guard]
                        cond = "if (impl_.guard(s_, e, GuardId::{})) ".format(gid)
                    body_lines.append(indent(6, "{}{{".format(cond) if cond else "{"))
                    body_lines.append(indent(7, "on_transition(s_, State::{}, e);".format(PSEUDO_FINAL_STATE)))
                    for ln in emit_exit_chain_for_state(s):
                        body_lines.append(indent(7, ln))
                    if t.action:
                        aid = action_map[t.action]
                        body_lines.append(indent(7, "impl_.action(s_, e, ActionId::{});".format(aid)))
                    body_lines.append(indent(7, "impl_.on_entry(State::{});".format(PSEUDO_FINAL_STATE)))
                    body_lines.append(indent(7, "s_ = State::{};".format(PSEUDO_FINAL_STATE)))
                    body_lines.append(indent(7, "terminated_ = true;"))
                    body_lines.append(indent(7, "return;"))
                    body_lines.append(indent(6, "}"))
                    continue

                dest_leaf = m.initial_leaf(t.dst) if m.is_composite(t.dst) else t.dst
                exit_nodes: List[str] = []
                n = m.nodes[s]
                source_node = m.nodes.get(t.src)
                while n and (source_node is None or n.name != source_node.name):
                    append_state(exit_nodes, n.name)
                    n = n.parent
                dest_within_source = False
                if t.src in m.nodes:
                    dn = m.nodes[dest_leaf]
                    while dn:
                        if dn.name == t.src:
                            dest_within_source = True
                            break
                        dn = dn.parent
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
                exit_common = False
                if (not t.internal) and dest_within_source and t.src == t.dst:
                    exit_common = True
                if dest_within_source and source_node is not None:
                    entry_anchor_name = t.src
                else:
                    lca_node = lca_src_dest if lca_src_dest is not None else (source_node if source_node is not None else None)
                    entry_anchor_name = lca_node.name if lca_node is not None else "__root__"
                entry_nodes = entry_chain_nodes(entry_anchor_name, dest_leaf)
                cond = ""
                if t.guard:
                    gid = guard_map[t.guard]
                    cond = "if (impl_.guard(s_, e, GuardId::{})) ".format(gid)
                body_lines.append(indent(6, "{}{{".format(cond) if cond else "{"))
                body_lines.append(indent(7, "on_transition(s_, State::{}, e);".format(state_ids_map[dest_leaf])))
                for en in exit_nodes:
                    node = m.nodes[en]
                    node_id = state_ids_map[node.name]
                    for act in node.exit_actions:
                        aid = action_map[act]
                        body_lines.append(indent(7, "impl_.action(State::{}, e, ActionId::{});".format(node_id, aid)))
                    body_lines.append(indent(7, "impl_.on_exit(State::{});".format(node_id)))
                if t.action:
                    aid = action_map[t.action]
                    body_lines.append(indent(7, "impl_.action(s_, e, ActionId::{});".format(aid)))
                if exit_common and source_node is not None and source_node.name != "__root__":
                    source_id = state_ids_map[source_node.name]
                    body_lines.append(indent(7, "impl_.on_entry(State::{});".format(source_id)))
                    for act in source_node.entry_actions:
                        aid = action_map[act]
                        body_lines.append(indent(7, "impl_.action(State::{}, e, ActionId::{});".format(source_id, aid)))
                for en in entry_nodes:
                    node = m.nodes[en]
                    node_id = state_ids_map[node.name]
                    body_lines.append(indent(7, "impl_.on_entry(State::{});".format(node_id)))
                    for act in node.entry_actions:
                        aid = action_map[act]
                        body_lines.append(indent(7, "impl_.action(State::{}, e, ActionId::{});".format(node_id, aid)))
                body_lines.append(indent(7, "s_ = State::{};".format(state_ids_map[dest_leaf])))
                body_lines.append(indent(7, "return;"))
                body_lines.append(indent(6, "}"))
            body_lines.append(indent(6, "return;"))
            event_blocks.append({
                "name": event_ids_map[ev],
                "lines": body_lines
            })
        state_cases.append({
            "name": state_ids_map[s],
            "events": event_blocks
        })

    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)), trim_blocks=True, lstrip_blocks=True)
    template = env.get_template("cpp_header.j2")

    code = template.render(
        machine_name=machine_name,
        states=[state_ids_map[s] for s in states] or ["__None"],
        events=[event_ids_map[e] for e in events] or ["__None"],
        guard_ids=guard_ids if guard_ids else ["__None"],
        action_ids=action_ids if action_ids else ["__None"],
        reset_lines=reset_lines,
        state_cases=state_cases,
        start_lines=start_lines,
        start_target_state=start_target_state,
        pseudo_initial=PSEUDO_INITIAL_STATE,
        pseudo_final=PSEUDO_FINAL_STATE
    )
    return code

def generate(input_path: Path, output_path: Path, machine_name: str = "StateSurfMachine") -> None:
    model = parse_puml(input_path)
    code = gen_header(model, machine_name)
    output_path.write_text(code, encoding="utf-8")

def main(argv):
    import argparse
    ap = argparse.ArgumentParser(description="StateSurf minimal generator (v1 subset)")
    sub = ap.add_subparsers(dest="cmd")
    g = sub.add_parser("generate")
    g.add_argument("-i", "--input", required=True)
    g.add_argument("-o", "--output", required=True)
    g.add_argument("-n", "--name", default="StateSurfMachine")
    v = sub.add_parser("validate")
    v.add_argument("-i", "--input", required=True)
    args = ap.parse_args(argv)
    if args.cmd == "generate":
        generate(Path(args.input), Path(args.output), args.name)
        return 0
    elif args.cmd == "validate":
        parse_puml(Path(args.input))
        print("OK")
        return 0
    else:
        ap.print_help()
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))
