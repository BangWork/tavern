from .exceptions import InvalidBuildInComparatorError, DuplicateAliasError, InvalidAliasTypeError
from .import_util import import_ext_function
from .compat import basestring


class ComparatorManager(object):
    def __init__(self):
        self._comparators = {}

    def add_comparator(self, aliases, comparator):
        if isinstance(aliases, basestring):
            aliases = [aliases]
        if not isinstance(aliases, (list, tuple)):
            raise InvalidAliasTypeError(
                "Aliases type should be string ,list or tuple", type(aliases))

        for alias in aliases:
            if alias in self._comparators:
                raise DuplicateAliasError(
                    "Alias {} is already defined in other comparator".format(alias))
            self._comparators[alias] = comparator

    def _get_uniform_comparator(self, comparator):
        """ convert comparator alias to uniform name
        """
        if comparator in ["eq", "equals", "==", "is"]:
            return "equals"
        elif comparator in ["lt", "less_than"]:
            return "less_than"
        elif comparator in ["le", "less_than_or_equals"]:
            return "less_than_or_equals"
        elif comparator in ["gt", "greater_than"]:
            return "greater_than"
        elif comparator in ["ge", "greater_than_or_equals"]:
            return "greater_than_or_equals"
        elif comparator in ["ne", "not_equals"]:
            return "not_equals"
        elif comparator in ["str_eq", "string_equals"]:
            return "string_equals"
        elif comparator in ["len_eq", "length_equals", "count_eq"]:
            return "length_equals"
        elif comparator in ["len_gt", "count_gt", "length_greater_than", "count_greater_than"]:
            return "length_greater_than"
        elif comparator in ["len_ge", "count_ge", "length_greater_than_or_equals",
                            "count_greater_than_or_equals"]:
            return "length_greater_than_or_equals"
        elif comparator in ["len_lt", "count_lt", "length_less_than", "count_less_than"]:
            return "length_less_than"
        elif comparator in ["len_le", "count_le", "length_less_than_or_equals",
                            "count_less_than_or_equals"]:
            return "length_less_than_or_equals"
        elif comparator in ["jsonschema", "jsonschema_validation", "jv"]:
            return "jsonschema_validation"
        elif comparator in ["unique_item_properties", "uip"]:
            return "unique_item_properties"

    def get_comparator(self, alias):
        built_in_comparator = self._get_uniform_comparator(alias)

        if built_in_comparator is not None:
            return import_ext_function(built_in_comparator)

        if alias not in self._comparators:
            raise InvalidBuildInComparatorError(
                "unknown comparator keyword:{}".format(alias))

        return self._comparators[alias]


comparators = ComparatorManager()
