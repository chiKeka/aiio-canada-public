from __future__ import annotations


ARCHETYPES = {
    "industrial_factory_proxy": "BCPI_FACTORY_",
    "institutional_buildings": "BCPI_INSTITUTIONAL_BUILDINGS_62213_",
    "schools": "BCPI_SCHOOL_",
    "municipal_operations_bus_depot": (
        "BCPI_BUS_DEPOT_WITH_MAINTENANCE_AND_REPAIR_FACILITIES_"
    ),
}

COMPONENT_SUFFIXES = {
    "concrete": "CONCRETE",
    "structural_steel_framing": "STRUCTURAL_STEEL_FRAMING",
    "electrical_systems": "ELECTRICAL",
    "hvac": "HEATING_VENTILATION_AND_AIR_CONDITIONING",
}


def material_indicator_targets() -> dict[str, tuple[str, str]]:
    return {
        f"{prefix}{suffix}": (archetype, component)
        for archetype, prefix in ARCHETYPES.items()
        for component, suffix in COMPONENT_SUFFIXES.items()
    }
