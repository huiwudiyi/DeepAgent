import json
from copy import deepcopy


TYPE_MAP = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list": list,
    "dict": dict,
}


def create_class_from_config(config_path: str):
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    class_name = config["class_name"]
    fields = config["fields"]

    attrs = {}
    annotations = {}

    def check_type(field_name, value, expected_type, type_name):
        if value is not None and not isinstance(value, expected_type):
            raise TypeError(
                f"{field_name} 类型错误，期望 {type_name}，"
                f"实际是 {type(value).__name__}"
            )

    def __init__(self, **kwargs):
        for field_name, field_config in fields.items():
            type_name = field_config["type"]
            default_value = field_config.get("default", None)

            expected_type = TYPE_MAP.get(type_name)
            if expected_type is None:
                raise TypeError(f"不支持的类型: {type_name}")

            value = kwargs.get(field_name, default_value)

            if isinstance(value, (list, dict)):
                value = deepcopy(value)

            check_type(field_name, value, expected_type, type_name)

            setattr(self, f"_{field_name}", value)

    def to_dict(self):
        data = {}

        for field_name in fields.keys():
            value = getattr(self, f"_{field_name}")

            if isinstance(value, (list, dict)):
                value = deepcopy(value)

            data[field_name] = value

        return data

    def save(self, save_path: str):
        data = self.to_dict()

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=4
            )

    attrs["__init__"] = __init__
    attrs["to_dict"] = to_dict
    attrs["save"] = save

    for field_name, field_config in fields.items():
        type_name = field_config["type"]
        expected_type = TYPE_MAP[type_name]
        annotations[field_name] = expected_type

        def make_getter(name):
            def getter(self):
                return getattr(self, f"_{name}")

            return getter

        def make_setter(name, expected_type, type_name):
            def setter(self, value):
                check_type(name, value, expected_type, type_name)

                if isinstance(value, (list, dict)):
                    value = deepcopy(value)

                setattr(self, f"_{name}", value)

            return setter

        attrs[f"get_{field_name}"] = make_getter(field_name)

        attrs[f"set_{field_name}"] = make_setter(
            field_name,
            expected_type,
            type_name
        )

        if type_name == "list":
            def make_append_method(name):
                def append_method(self, value):
                    current_value = getattr(self, f"_{name}")

                    if current_value is None:
                        current_value = []
                        setattr(self, f"_{name}", current_value)

                    if not isinstance(current_value, list):
                        raise TypeError(f"{name} 当前不是 list 类型")

                    current_value.append(value)

                return append_method

            attrs[f"append_{field_name}"] = make_append_method(field_name)

        if type_name == "dict":
            def make_set_item_method(name):
                def set_item_method(self, key, value):
                    current_value = getattr(self, f"_{name}")

                    if current_value is None:
                        current_value = {}
                        setattr(self, f"_{name}", current_value)

                    if not isinstance(current_value, dict):
                        raise TypeError(f"{name} 当前不是 dict 类型")

                    current_value[key] = value

                return set_item_method

            attrs[f"set_{field_name}_item"] = make_set_item_method(field_name)

    attrs["__annotations__"] = annotations

    return type(class_name, (object,), attrs)