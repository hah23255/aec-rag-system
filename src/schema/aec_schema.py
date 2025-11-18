"""
AEC Graph Schema for Design Management RAG System

Defines 7 entity types and 10 relationship types for modeling
architectural/engineering project knowledge graphs.

Entity Types:
    - Drawing: CAD drawings, BIM models
    - Component: Building elements (walls, doors, HVAC, etc.)
    - Room: Physical spaces
    - Decision: Design changes, RFIs, change orders
    - Person: Project team members
    - Requirement: Code requirements, standards
    - Milestone: Project phases, deadlines

Relationship Types:
    - SUPERSEDES: Version control (newer drawing → older)
    - AFFECTS: Impact relationships between drawings
    - CONTAINS: Drawing contains components
    - LOCATED_IN: Component in room
    - REQUIRES: Component requires code compliance
    - APPROVED_BY: Decision/drawing approved by person
    - MADE_BY: Decision made by person
    - MODIFIES: Decision modifies component/drawing
    - REFERENCES: Drawing references another
    - SUBMITTED_AT: Drawing submitted at milestone
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

# =============================================================================
# Enumerations
# =============================================================================


class DrawingDiscipline(str, Enum):
    """Architectural/engineering disciplines"""

    ARCHITECTURAL = "A"
    STRUCTURAL = "S"
    MECHANICAL = "M"
    ELECTRICAL = "E"
    PLUMBING = "P"
    CIVIL = "C"
    LANDSCAPE = "L"
    FIRE_PROTECTION = "FP"


class DrawingStatus(str, Enum):
    """Drawing lifecycle status"""

    DRAFT = "draft"
    ISSUED = "issued"
    APPROVED = "approved"
    SUPERSEDED = "superseded"
    VOID = "void"


class ComponentType(str, Enum):
    """Building component categories"""

    WALL = "wall"
    DOOR = "door"
    WINDOW = "window"
    ROOF = "roof"
    FLOOR = "floor"
    CEILING = "ceiling"
    HVAC = "hvac"
    STRUCTURAL = "structural"
    PLUMBING = "plumbing"
    ELECTRICAL = "electrical"
    FIRE_PROTECTION = "fire_protection"


# =============================================================================
# Entity Classes (Nodes)
# =============================================================================


@dataclass
class Drawing:
    """
    Represents a CAD drawing or BIM model.

    Attributes:
        id: Unique identifier (e.g., "A-101-v3")
        drawing_number: Drawing number (e.g., "A-101")
        version: Version/revision (e.g., "3", "C", "REV3")
        discipline: A, S, M, E, P, C, etc.
        title: Full drawing title
        date: Issue date
        file_path: Path to DWG/PDF file
        file_type: "dwg", "dxf", "pdf", "rvt"
        scale: Drawing scale (e.g., "1/4\" = 1'-0\"")
        sheet_size: "A1", "A3", "D", etc.
        status: draft, issued, approved, superseded
        description: Long-form description/notes
        embedding_id: Reference to vector embedding
    """

    id: str
    drawing_number: str
    version: str
    discipline: DrawingDiscipline
    title: str
    date: datetime
    file_path: str
    file_type: str
    scale: Optional[str] = None
    sheet_size: Optional[str] = None
    status: DrawingStatus = DrawingStatus.DRAFT
    description: Optional[str] = None
    embedding_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with datetime serialization"""
        data = asdict(self)
        data["date"] = self.date.isoformat()
        data["discipline"] = self.discipline.value
        data["status"] = self.status.value
        return data


@dataclass
class Component:
    """
    Building element or assembly.

    Attributes:
        id: Unique identifier (e.g., "WA-02")
        type: Component category
        name: Component name/designation
        specification: Reference to spec section (e.g., "09 21 16")
        description: Detailed description
        manufacturer: Manufacturer name
        model: Model number
        quantity: Quantity in project
        unit: Unit of measurement (SF, LF, EA, etc.)
        cost_estimate: Estimated cost
        embedding_id: Reference to vector embedding
    """

    id: str
    type: ComponentType
    name: str
    description: str
    specification: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    cost_estimate: Optional[float] = None
    embedding_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["type"] = self.type.value
        return data


@dataclass
class Room:
    """
    Physical space or zone in the building.

    Attributes:
        id: Unique identifier (e.g., "R-101")
        number: Room number (e.g., "101")
        name: Room name (e.g., "Lobby")
        floor: Floor level (e.g., "1", "Ground", "B1")
        area: Area in square feet/meters
        use_type: "office", "lobby", "mechanical", etc.
        occupancy_class: IBC occupancy classification
        capacity: Occupant load
        finish_schedule: Reference to finish schedule
        embedding_id: Reference to vector embedding
    """

    id: str
    number: str
    name: str
    floor: str
    area: float
    use_type: str
    occupancy_class: Optional[str] = None
    capacity: Optional[int] = None
    finish_schedule: Optional[str] = None
    embedding_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class Decision:
    """
    Design decision, change order, or RFI response.

    Attributes:
        id: Unique identifier (e.g., "DEC-2025-034")
        type: "design_change", "rfi_response", "change_order", etc.
        date: Decision date
        title: Short title
        description: Full description/rationale
        impact: "cost", "schedule", "design", "code_compliance"
        status: "pending", "approved", "rejected", "implemented"
        cost_impact: Cost change (+ or -)
        schedule_impact: Days added/removed
        embedding_id: Reference to vector embedding
    """

    id: str
    type: str  # design_change, rfi_response, change_order, clarification
    date: datetime
    title: str
    description: str
    impact: str  # comma-separated: cost, schedule, design
    status: str  # pending, approved, rejected, implemented
    cost_impact: Optional[float] = None
    schedule_impact: Optional[int] = None  # days
    embedding_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with datetime serialization"""
        data = asdict(self)
        data["date"] = self.date.isoformat()
        return data


@dataclass
class Person:
    """
    Project team member.

    Attributes:
        id: Unique identifier (e.g., "PER-jsmith")
        name: Full name
        role: "architect", "structural_engineer", "pm", etc.
        company: Company/firm name
        email: Email address
        phone: Phone number
        discipline: Primary discipline (A, S, M, E, P, C)
        active: Currently on project?
    """

    id: str
    name: str
    role: str
    company: str
    email: Optional[str] = None
    phone: Optional[str] = None
    discipline: Optional[str] = None
    active: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class Requirement:
    """
    Code requirement, standard, or specification constraint.

    Attributes:
        id: Unique identifier (e.g., "REQ-IBC-705")
        type: "code", "standard", "spec", "owner_requirement"
        source: "IBC 2021", "ASHRAE 90.1", "ACI 318", etc.
        section: Section/clause reference
        description: Requirement text
        value: Specific value/criterion (e.g., "2-hour")
        applies_to: What it applies to (e.g., "fire_walls")
        embedding_id: Reference to vector embedding
    """

    id: str
    type: str  # code, standard, spec, owner_requirement
    source: str
    section: str
    description: str
    value: Optional[str] = None
    applies_to: Optional[str] = None
    embedding_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class Milestone:
    """
    Project phase, submission, or deadline.

    Attributes:
        id: Unique identifier (e.g., "MS-DD")
        name: Milestone name (e.g., "Design Development")
        abbreviation: "SD", "DD", "CD", "CA"
        date: Target/actual date
        status: "upcoming", "in_progress", "completed"
        percentage_complete: 0-100
        description: Description
    """

    id: str
    name: str
    abbreviation: str
    date: datetime
    status: str  # upcoming, in_progress, completed
    percentage_complete: float = 0.0
    description: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with datetime serialization"""
        data = asdict(self)
        data["date"] = self.date.isoformat()
        return data


# =============================================================================
# Relationship Classes (Edges)
# =============================================================================


@dataclass
class Supersedes:
    """Newer drawing supersedes older drawing"""

    date: datetime
    reason: str
    changes_summary: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with datetime serialization"""
        data = asdict(self)
        data["date"] = self.date.isoformat()
        return data


@dataclass
class Affects:
    """One drawing affects another"""

    impact_type: str  # coordination, conflict, dependency
    severity: str  # minor, moderate, major
    description: str
    resolved: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class Contains:
    """Drawing contains component"""

    quantity: Optional[float] = None
    detail_reference: Optional[str] = None
    note: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class LocatedIn:
    """Component located in room"""

    quantity: Optional[float] = None
    installation_notes: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class Requires:
    """Component requires a requirement"""

    compliance_status: str  # compliant, non_compliant, under_review
    verification_method: Optional[str] = None
    verified_by: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class ApprovedBy:
    """Decision/Drawing approved by person"""

    date: datetime
    signature_path: Optional[str] = None
    comments: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with datetime serialization"""
        data = asdict(self)
        data["date"] = self.date.isoformat()
        return data


@dataclass
class MadeBy:
    """Decision made by person"""

    date: datetime
    rationale: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with datetime serialization"""
        data = asdict(self)
        data["date"] = self.date.isoformat()
        return data


@dataclass
class Modifies:
    """Decision modifies component/drawing"""

    change_type: str  # addition, deletion, modification
    before_state: Optional[str] = None
    after_state: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class References:
    """Drawing references another drawing"""

    reference_type: str  # detail, section, elevation, plan
    sheet_reference: Optional[str] = None
    note: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class SubmittedAt:
    """Drawing submitted at milestone"""

    date: datetime
    review_status: str  # approved, approved_with_comments, resubmit
    comments_path: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with datetime serialization"""
        data = asdict(self)
        data["date"] = self.date.isoformat()
        return data


# =============================================================================
# Schema Utilities
# =============================================================================

# Entity type registry
ENTITY_TYPES = {
    "Drawing": Drawing,
    "Component": Component,
    "Room": Room,
    "Decision": Decision,
    "Person": Person,
    "Requirement": Requirement,
    "Milestone": Milestone,
}

# Relationship type registry
RELATIONSHIP_TYPES = {
    "SUPERSEDES": Supersedes,
    "AFFECTS": Affects,
    "CONTAINS": Contains,
    "LOCATED_IN": LocatedIn,
    "REQUIRES": Requires,
    "APPROVED_BY": ApprovedBy,
    "MADE_BY": MadeBy,
    "MODIFIES": Modifies,
    "REFERENCES": References,
    "SUBMITTED_AT": SubmittedAt,
}


def serialize_entity(entity: Any) -> str:
    """Serialize entity to JSON string"""
    return json.dumps(entity.to_dict(), indent=2)


def serialize_relationship(rel: Any) -> str:
    """Serialize relationship to JSON string"""
    return json.dumps(rel.to_dict(), indent=2)
