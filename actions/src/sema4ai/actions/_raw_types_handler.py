class _RawTypesHandler:
    def __init__(self, param_name: str, pydantic_class: type):
        self.param_name = param_name
        self.pydantic_class = pydantic_class

    def model_json_schema(self, **kwargs):
        ret = self.pydantic_class.model_json_schema(**kwargs)
        return ret["properties"][self.param_name]

    def model_validate(self, value, **kwargs):
        value = {self.param_name: value}
        ret = self.pydantic_class.model_validate(value, **kwargs)
        return getattr(ret, self.param_name)


_cache = {}


def _obtain_raw_types_handler(param_name: str, param_type: type) -> _RawTypesHandler:
    key = repr(param_type)
    if key not in _cache:
        try:
            from pydantic import BaseModel

            name_to_type_annotations = {param_name: param_type}

            # This will create a pydantic class with the given type annotations
            # (so that we can use pydantic methods from the runtime information).
            class NewClass(BaseModel):
                __annotations__ = name_to_type_annotations

            # This will wrap the pydantic class and massage the methods we're
            # interested in and then use the actual raw types wrapped in the param_name
            # as we don't want to actually use the pydantic class (the use case here
            # is the user declaring something as list[int] directly as an argument
            # without having to create a pydantic class for it).

            _cache[key] = _RawTypesHandler(param_name, NewClass)
        except Exception:
            raise
    return _cache[key]
