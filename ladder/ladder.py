import argparse
from pathlib import Path


ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
COMPONENTS_DIR = DATA_DIR / "components"
AUDIENCES_DIR = DATA_DIR / "audiences"
OUTPUT_DIR = ROOT / "outputs"

COMPONENT_REQUIRED_FIELDS = [
    "name",
    "layer",
    "status",
    "one_line",
    "problem",
    "inputs",
    "outputs",
    "dependencies",
    "example",
    "audience_value",
    "next_rung",
    "limitations",
]

AUDIENCE_REQUIRED_FIELDS = [
    "id",
    "name",
    "description",
    "vocabulary_level",
    "omit",
    "lead_with",
    "frame",
    "prior_knowledge",
    "first_questions",
    "desired_outcome",
]

ECOSYSTEM_REQUIRED_FIELDS = [
    "system_name",
    "tagline",
    "what_it_is",
    "why_it_matters",
    "local_first_note",
    "lineage",
    "meta_note",
    "layers",
    "components_in_order",
    "overview_next_rung",
]

VALID_STATUSES = {"proposal", "in-progress", "built"}
VALID_VOCABULARY = {"plain", "accessible", "technical"}


class SimpleYAMLParser:
    def __init__(self, text: str):
        self.lines = text.splitlines()
        self.index = 0

    def parse(self):
        return self.parse_block(0)

    def parse_block(self, indent: int):
        first = self.peek_nonempty()
        if first is None:
            return {}
        current_indent, content = first
        if current_indent < indent:
            return {}
        if content.startswith("- "):
            return self.parse_list(indent)
        return self.parse_mapping(indent)

    def parse_mapping(self, indent: int):
        result = {}
        while True:
            item = self.peek_nonempty()
            if item is None:
                break
            current_indent, content = item
            if current_indent < indent:
                break
            if current_indent != indent:
                raise ValueError(f"unexpected indentation at line {self.index + 1}")
            if content.startswith("- "):
                break

            self.index += 1
            if ":" not in content:
                raise ValueError(f"expected key/value pair at line {self.index}")
            key, remainder = content.split(":", 1)
            key = key.strip()
            remainder = remainder.lstrip()

            if remainder == ">":
                result[key] = self.parse_folded(indent)
            elif remainder == "":
                result[key] = self.parse_nested(indent + 2)
            else:
                result[key] = self.parse_scalar(remainder)
        return result

    def parse_list(self, indent: int):
        result = []
        while True:
            item = self.peek_nonempty()
            if item is None:
                break
            current_indent, content = item
            if current_indent < indent:
                break
            if current_indent != indent or not content.startswith("- "):
                break

            self.index += 1
            remainder = content[2:].strip()
            if remainder == "":
                result.append(self.parse_nested(indent + 2))
                continue

            if ":" in remainder:
                key, value = remainder.split(":", 1)
                key = key.strip()
                value = value.lstrip()
                item_value = {key: self.parse_scalar(value) if value else None}
                extra = self.collect_list_item_mapping(indent + 2)
                item_value.update(extra)
                result.append(item_value)
                continue

            result.append(self.parse_scalar(remainder))
        return result

    def collect_list_item_mapping(self, indent: int):
        result = {}
        while True:
            item = self.peek_nonempty()
            if item is None:
                break
            current_indent, content = item
            if current_indent < indent:
                break
            if current_indent != indent:
                raise ValueError(f"unexpected indentation at line {self.index + 1}")
            if content.startswith("- "):
                break

            self.index += 1
            if ":" not in content:
                raise ValueError(f"expected key/value pair at line {self.index}")
            key, remainder = content.split(":", 1)
            key = key.strip()
            remainder = remainder.lstrip()
            if remainder == ">":
                result[key] = self.parse_folded(indent)
            elif remainder == "":
                result[key] = self.parse_nested(indent + 2)
            else:
                result[key] = self.parse_scalar(remainder)
        return result

    def parse_nested(self, indent: int):
        item = self.peek_nonempty()
        if item is None:
            return {}
        current_indent, content = item
        if current_indent < indent:
            return {}
        if content.startswith("- "):
            return self.parse_list(indent)
        return self.parse_mapping(indent)

    def parse_folded(self, parent_indent: int):
        parts = []
        while True:
            item = self.peek_nonempty(include_blank=True)
            if item is None:
                break
            current_indent, content, is_blank = item
            if is_blank:
                self.index += 1
                if parts and parts[-1] != "":
                    parts.append("")
                continue
            if current_indent <= parent_indent:
                break
            self.index += 1
            parts.append(content.strip())
        text = " ".join(part for part in parts if part != "").strip()
        return text

    def parse_scalar(self, value: str):
        if value == "[]":
            return []
        if value in {"true", "false"}:
            return value == "true"
        return value

    def peek_nonempty(self, include_blank: bool = False):
        cursor = self.index
        while cursor < len(self.lines):
            raw = self.lines[cursor]
            if not raw.strip():
                if include_blank:
                    return (0, "", True)
                cursor += 1
                continue
            indent = len(raw) - len(raw.lstrip(" "))
            content = raw[indent:]
            if include_blank:
                return (indent, content, False)
            return (indent, content)
        return None


def load_yaml(path: Path) -> dict:
    if not path.exists():
        raise ValueError(f"missing file '{path}'")
    return SimpleYAMLParser(path.read_text(encoding="utf-8")).parse()


def validate_required(data: dict, name: str, required_fields: list, kind: str) -> None:
    for field in required_fields:
        if field not in data:
            raise ValueError(f"{kind} '{name}' is missing required field '{field}'")


def valid_audience_ids() -> list:
    return sorted(path.stem for path in AUDIENCES_DIR.glob("*.yaml"))


def load_component(name: str) -> dict:
    path = COMPONENTS_DIR / f"{name}.yaml"
    if not path.exists():
        valid = ", ".join(sorted(p.stem for p in COMPONENTS_DIR.glob("*.yaml")))
        raise ValueError(f"unknown component '{name}' — valid: {valid}")
    data = load_yaml(path)
    validate_component(data, name)
    return data


def load_audience(audience_id: str) -> dict:
    path = AUDIENCES_DIR / f"{audience_id}.yaml"
    if not path.exists():
        valid = ", ".join(sorted(p.stem for p in AUDIENCES_DIR.glob("*.yaml")))
        raise ValueError(f"unknown audience '{audience_id}' — valid: {valid}")
    data = load_yaml(path)
    validate_audience(data, audience_id)
    return data


def load_ecosystem() -> dict:
    data = load_yaml(DATA_DIR / "ecosystem.yaml")
    validate_ecosystem(data)
    return data


def validate_component(data: dict, name: str) -> None:
    validate_required(data, name, COMPONENT_REQUIRED_FIELDS, "component")
    if data["status"] not in VALID_STATUSES:
        raise ValueError(f"component '{name}' has invalid status '{data['status']}'")
    for field in ("inputs", "outputs", "dependencies", "limitations"):
        if not isinstance(data[field], list) or not data[field]:
            raise ValueError(f"component '{name}' field '{field}' must be a non-empty list")
    for field in ("audience_value", "next_rung"):
        if not isinstance(data[field], dict):
            raise ValueError(f"component '{name}' field '{field}' must be a mapping")
    for audience_id in valid_audience_ids():
        if audience_id not in data["audience_value"]:
            raise ValueError(f"component '{name}' is missing required field 'audience_value.{audience_id}'")
        if audience_id not in data["next_rung"]:
            raise ValueError(f"component '{name}' is missing required field 'next_rung.{audience_id}'")


def validate_audience(data: dict, audience_id: str) -> None:
    validate_required(data, audience_id, AUDIENCE_REQUIRED_FIELDS, "audience")
    if data["id"] != audience_id:
        raise ValueError(f"audience '{audience_id}' has mismatched id '{data['id']}'")
    if data["vocabulary_level"] not in VALID_VOCABULARY:
        raise ValueError(
            f"audience '{audience_id}' has invalid vocabulary_level '{data['vocabulary_level']}'"
        )


def validate_ecosystem(data: dict) -> None:
    validate_required(data, "ecosystem", ECOSYSTEM_REQUIRED_FIELDS, "ecosystem")
    if not isinstance(data["layers"], list) or not data["layers"]:
        raise ValueError("ecosystem 'ecosystem' field 'layers' must be a non-empty list")
    if not isinstance(data["components_in_order"], list) or not data["components_in_order"]:
        raise ValueError("ecosystem 'ecosystem' field 'components_in_order' must be a non-empty list")
    for audience_id in valid_audience_ids():
        if audience_id not in data["overview_next_rung"]:
            raise ValueError(f"ecosystem 'ecosystem' is missing required field 'overview_next_rung.{audience_id}'")


def bullet_list(items: list) -> str:
    return "\n".join(f"- {item}" for item in items)


def status_line(component: dict) -> str:
    if component["status"] == "built":
        return ""
    return (
        f"\nThis is {component['status'].replace('-', ' ')}, not a finished tool. "
        "It matters here because it shows where the system is trying to go next.\n"
    )


def component_card_body(component: dict, audience: dict) -> str:
    lines = [
        f"# {component['name']}",
        f"*{component['layer'].title()} layer · {component['status']}*",
        "",
        component["audience_value"][audience["id"]],
        "",
    ]
    if component["status"] != "built":
        lines.append(
            f"This is {component['status'].replace('-', ' ')}, not a finished tool. "
            "It matters here because it shows where the system is trying to go next."
        )
        lines.append("")
    lines.extend(
        [
            f"**What it is**: {component['one_line']}",
            "",
            f"**The problem it solves**: {component['problem']}",
            "",
            f"**A concrete example**: {component['example']}",
            "",
        ]
    )
    relationships = component.get("relationships", [])
    if relationships:
        lines.append("**How it fits**:")
        lines.extend(f"- {item}" for item in relationships)
        lines.append("")

    if audience["id"] == "collaborator":
        for label, key in (
            ("Inputs", "inputs"),
            ("Outputs", "outputs"),
            ("Dependencies", "dependencies"),
            ("Current limitations", "limitations"),
        ):
            lines.append(f"**{label}**:")
            lines.extend(f"- {item}" for item in component[key])
            lines.append("")
    else:
        lines.append("**What to keep in mind**:")
        lines.extend(f"- {item}" for item in component["limitations"])
        lines.append("")

    lines.append(f"**Next rung for you**: {component['next_rung'][audience['id']]}")
    return "\n".join(lines).strip() + "\n"


def layers_summary(ecosystem: dict) -> str:
    names = [layer["name"].lower() for layer in ecosystem["layers"]]
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + f", and {names[-1]}"


def collect_audience_limitations(components: list) -> list:
    seen = []
    for component in components:
        limitation = component["limitations"][0]
        if limitation not in seen:
            seen.append(limitation)
    return seen[:3]


def generate_component_card(component_name: str, audience_id: str) -> str:
    return component_card_body(load_component(component_name), load_audience(audience_id))


def generate_audience_explainer(audience_id: str) -> str:
    audience = load_audience(audience_id)
    ecosystem = load_ecosystem()
    spotlight_names = audience.get("spotlight_components", [])[:3]
    spotlight_components = [load_component(name) for name in spotlight_names]
    lines = [
        f"# {ecosystem['system_name']} for {audience['name']}",
        "",
        ecosystem["what_it_is"],
        "",
        ecosystem["lineage"],
        "",
        ecosystem["meta_note"],
        "",
        "## Why it matters for this audience",
        "",
        f"{audience['frame']}.",
        "",
        "The goal here is not to hand you a full technical architecture. "
        "It is to give you a reachable next rung into the system from where you actually are starting.",
        "",
        "## The system in brief",
        "",
        f"- {ecosystem['why_it_matters']}",
        f"- {ecosystem['local_first_note']}",
        f"- The work spans {layers_summary(ecosystem)}.",
        "",
        "## A few parts worth noticing",
        "",
    ]

    for component in spotlight_components:
        lines.extend(
            [
                f"### {component['name']}",
                "",
                component["audience_value"][audience["id"]],
                "",
                component["example"],
                "",
                f"Status: {'built and in active use' if component['status'] == 'built' else component['status'].replace('-', ' ')}.",
                "",
            ]
        )

    lines.extend(["## Honest limits", ""])
    lines.extend(f"- {item}" for item in collect_audience_limitations(spotlight_components))
    lines.extend(["", "## Next rung", "", ecosystem["overview_next_rung"][audience["id"]]])
    return "\n".join(lines).strip() + "\n"


def generate_ecosystem_overview() -> str:
    ecosystem = load_ecosystem()
    components = [load_component(name) for name in ecosystem["components_in_order"]]
    lines = [
        f"# {ecosystem['system_name']}",
        "",
        f"*{ecosystem['tagline']}*",
        "",
        ecosystem["what_it_is"],
        "",
        ecosystem["why_it_matters"],
        "",
        ecosystem["local_first_note"],
        "",
        ecosystem["lineage"],
        "",
        ecosystem["meta_note"],
        "",
        "## Layers",
        "",
    ]
    lines.extend(f"- **{layer['name']}**: {layer['description']}" for layer in ecosystem["layers"])
    lines.extend(["", "## What exists now", ""])
    for component in components:
        if component["status"] == "built":
            suffix = "(built)"
        elif component["status"] == "in-progress":
            suffix = "(in progress)"
        else:
            suffix = "(proposal)"
        lines.append(f"- **{component['name']}**: {component['one_line']} {suffix}")
    lines.extend(
        [
            "",
            "## Why Ladder belongs here",
            "",
            "`Ladder` is the communication layer because a people-first system has to stay explainable. "
            "The library as a ladder started as a service principle: meet people where they are and help them reach the next rung. "
            "In this ecosystem, that same principle shapes how technical knowledge work gets described, taught, and shared.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def write_output(path: Path, content: str) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"wrote {path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    generate = subparsers.add_parser("generate")
    generate.add_argument("--audience", required=True)
    generate.add_argument("--component")
    generate.add_argument("--overview", action="store_true")
    generate.add_argument("--all-components", action="store_true")
    generate.add_argument("--explainer", action="store_true")

    args = parser.parse_args()

    if args.command != "generate":
        parser.print_help()
        return

    load_audience(args.audience)

    if args.overview:
        write_output(OUTPUT_DIR / "ecosystem_overview.md", generate_ecosystem_overview())
        return

    if args.explainer:
        write_output(
            OUTPUT_DIR / f"audience_explainer__{args.audience}.md",
            generate_audience_explainer(args.audience),
        )
        return

    if args.component:
        write_output(
            OUTPUT_DIR / f"component_card__{args.component}__{args.audience}.md",
            generate_component_card(args.component, args.audience),
        )
        return

    if args.all_components:
        for path in sorted(COMPONENTS_DIR.glob("*.yaml")):
            component_name = path.stem
            write_output(
                OUTPUT_DIR / f"component_card__{component_name}__{args.audience}.md",
                generate_component_card(component_name, args.audience),
            )
        return

    raise ValueError("choose one of --overview, --explainer, --component, or --all-components")


if __name__ == "__main__":
    main()
