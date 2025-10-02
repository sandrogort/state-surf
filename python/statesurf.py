#!/usr/bin/env python3
import sys, re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

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

    states = [s for s in topo_states(m) if s!="__root__"]
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
        if st=="__root__": continue
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

    def enum(name: str, items: List[str]) -> str:
        if not items: items = ["__None"]
        body = ",\n  ".join(items)
        return "enum class {} {{\n  {}\n}};".format(name, body)

    # transitions map
    by_state = build_transitions_by_state(m)

    out = []
    out.append("#pragma once")
    out.append("// Generated by StateSurf minimal generator (v1 subset). C++11 header-only.")
    out.append("namespace statesurf {")
    out.append(enum("State", [sanitize_id(s) for s in states]))
    out.append(enum("Event", [sanitize_id(e) for e in events]))
    out.append(enum("GuardId", guard_ids))
    out.append(enum("ActionId", action_ids))
    out.append("struct IHooks {")
    out.append("  virtual ~IHooks() {}")
    out.append("  virtual void on_entry(State) = 0;")
    out.append("  virtual void on_exit(State) = 0;")
    out.append("  virtual bool guard(State, Event, GuardId) = 0;")
    out.append("  virtual void action(State, Event, ActionId) = 0;")
    out.append("};")
    out.append("inline void on_event(State, Event) {}")
    out.append("inline void on_transition(State, State, Event) {}")

    # helper functions for entry/exit chains per state
    def emit_exit_chain_for_state(sname: str) -> List[str]:
        lines=[]
        n = m.nodes[sname]
        while n and n.name!="__root__":
            for act in n.exit_actions:
                aid = action_map[act]
                lines.append("impl_.action(State::{}, e, ActionId::{});".format(sanitize_id(n.name), aid))
            lines.append("impl_.on_exit(State::{});".format(sanitize_id(n.name)))
            n = n.parent
        return lines

    def append_state(lst: List[str], name: str):
        if name != "__root__":
            lst.append(name)

    def entry_chain_nodes(from_lca_name: str, dest_leaf: str) -> List[str]:
        # nodes from child under lca to dest leaf, excluding __root__
        acc=[]
        n = m.nodes[dest_leaf]
        while n and n.name != from_lca_name:
            if n.name != "__root__":
                acc.append(n.name)
            n = n.parent
        acc.reverse()
        return acc

    out.append("class {} {{".format(machine_name))
    out.append("public:")
    out.append("  explicit {}(IHooks& impl) : impl_(impl) {{ reset(); }}".format(machine_name))
    out.append("  void reset() {")
    out.append("    terminated_ = false;")
    # root initial
    root_init = m.root.initial_target
    if root_init is None and states:
        root_init = states[0]
    if root_init:
        # walk to leaf via composite initials
        leaf = m.initial_leaf(root_init)
        # entry chain from top under __root__ to leaf
        path = []
        n = m.nodes[leaf]
        while n and n.name!="__root__":
            path.append(n)
            n = n.parent
        path_nodes = list(reversed(path))
        first_child = {}
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
                    out.append("    impl_.action(State::{}, Event{{}}, ActionId::{});".format(sanitize_id(action_state), aid))
            out.append("    impl_.on_entry(State::{});".format(sanitize_id(node.name)))
            for act in node.entry_actions:
                aid = action_map[act]
                out.append("    impl_.action(State::{}, Event{{}}, ActionId::{});".format(sanitize_id(node.name), aid))
        out.append("    s_ = State::{};".format(sanitize_id(leaf)))
    out.append("  }")
    out.append("  State state() const { return s_; }")
    out.append("  bool terminated() const { return terminated_; }")
    out.append("  void dispatch(Event e) {")
    out.append("    if (terminated_) return;")
    out.append("    on_event(s_, e);")
    out.append("    switch (s_) {")
    for s in states:
        out.append("      case State::{}: {{".format(sanitize_id(s)))
        evmap = by_state.get(s, {})
        if not evmap:
            out.append("        return;")
            out.append("      }")
            continue
        out.append("        switch (e) {")
        for ev, lst in evmap.items():
            out.append("          case Event::{}: {{".format(sanitize_id(ev)))
            any_rule=False
            for t in lst:
                if t.internal:
                    cond = ""
                    if t.guard:
                        gid = guard_map[t.guard]
                        cond = "if (impl_.guard(s_, e, GuardId::{})) ".format(gid)
                    out.append("            {}{{".format(cond) if cond else "            {")
                    out.append("              on_transition(s_, s_, e);")
                    if t.action:
                        aid = action_map[t.action]
                        out.append("              impl_.action(s_, e, ActionId::{});".format(aid))
                    out.append("              return;")
                    out.append("            }")
                    continue
                # destination
                if t.dst is None:
                    # final
                    cond = ""
                    if t.guard:
                        gid = guard_map[t.guard]
                        cond = "if (impl_.guard(s_, e, GuardId::{})) ".format(gid)
                    out.append("            {}{{".format(cond) if cond else "            {")
                    out.append("              on_transition(s_, s_, e);")
                    # exit all from current s
                    for ln in emit_exit_chain_for_state(s):
                        out.append("              " + ln)
                    if t.action:
                        aid = action_map[t.action]
                        out.append("              impl_.action(s_, e, ActionId::{});".format(aid))
                    out.append("              terminated_ = true;")
                    out.append("              return;")
                    out.append("            }")
                    any_rule=True
                    continue
                dest_leaf = m.initial_leaf(t.dst) if m.is_composite(t.dst) else t.dst
                exit_nodes=[]
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
                out.append("            {}{{".format(cond) if cond else "            {")
                out.append("              on_transition(s_, State::{}, e);".format(sanitize_id(dest_leaf)))
                # exit nodes
                for en in exit_nodes:
                    node = m.nodes[en]
                    for act in node.exit_actions:
                        aid = action_map[act]
                        out.append("              impl_.action(State::{}, e, ActionId::{});".format(sanitize_id(node.name), aid))
                    out.append("              impl_.on_exit(State::{});".format(sanitize_id(node.name)))
                # transition action
                if t.action:
                    aid = action_map[t.action]
                    out.append("              impl_.action(s_, e, ActionId::{});".format(aid))
                # entry nodes
                if exit_common and source_node is not None and source_node.name != "__root__":
                    node = source_node
                    out.append("              impl_.on_entry(State::{});".format(sanitize_id(node.name)))
                    for act in node.entry_actions:
                        aid = action_map[act]
                        out.append("              impl_.action(State::{}, e, ActionId::{});".format(sanitize_id(node.name), aid))
                for en in entry_nodes:
                    node = m.nodes[en]
                    out.append("              impl_.on_entry(State::{});".format(sanitize_id(node.name)))
                    for act in node.entry_actions:
                        aid = action_map[act]
                        out.append("              impl_.action(State::{}, e, ActionId::{});".format(sanitize_id(node.name), aid))
                out.append("              s_ = State::{};".format(sanitize_id(dest_leaf)))
                out.append("              return;")
                out.append("            }")
                any_rule=True
            out.append("            return;")
            out.append("          }")
        out.append("          default: return;")
        out.append("        }")
        out.append("      }")
    out.append("    }")
    out.append("  }")
    out.append("private:")
    out.append("  IHooks& impl_;")
    out.append("  State s_;")
    out.append("  bool terminated_ = false;")
    out.append("};")
    out.append("} // namespace statesurf")
    return "\n".join(out)

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
