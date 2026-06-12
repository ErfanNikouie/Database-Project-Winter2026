FILTER_HELP_BY_TYPE: dict[str, str] = {
    "Integer": "Examples: >5, (<10 & !=3), (!=10 | =2)",
    "Double": "Examples: >5.5, <=100.25",
    "Decimal": "Examples: >1000, (>=500 & <2000)",
    "Date": "ISO date, e.g. >=2026-01-01",
    "DateTime": "ISO datetime, e.g. >=2026-01-01T10:00:00",
    "String": "Use exact values, OR with |, or comma shorthand: John|Ali or John,Ali",
    "Text": "Same as String",
    "Boolean": "True or False",
    "Lookup": "Use lookup IDs. Supports | and !=",
    "ForeignKey": "Use referenced IDs. Supports numeric expressions like >5 & <10",
}

