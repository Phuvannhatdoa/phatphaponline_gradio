"""Kiểm YAML frontmatter của agent: parse được, không trùng khóa, không "*": allow."""
import sys
import yaml


class StrictLoader(yaml.SafeLoader):
    pass


def _no_dup_mapping(loader, node, deep=False):
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise yaml.constructor.ConstructorError(
                None, None, f"khóa trùng: {key!r}", key_node.start_mark)
        seen.add(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep)


StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_dup_mapping)

ok = True
for path in sys.argv[1:]:
    text = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    parts = text.split("---\n", 2)
    fm = yaml.load(parts[1], Loader=StrictLoader)
    perm = fm["permission"]
    bad = [k for k, v in perm.get("bash", {}).items() if k == "*" and v == "allow"]
    bad += [k for k, v in perm.get("edit", {}).items() if k == "*" and v == "allow"] if isinstance(perm.get("edit"), dict) else []
    if isinstance(perm.get("edit"), str) and perm["edit"] == "allow":
        bad.append("edit: allow (toàn cục)")
    print(path.split("\\")[-1], "OK" if not bad else f"FAIL {bad}")
    print(yaml.dump(perm, allow_unicode=True, sort_keys=False).rstrip())
    ok = ok and not bad
sys.exit(0 if ok else 1)
