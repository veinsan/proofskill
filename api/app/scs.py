"""SCS Skill Catalog service: API-08 listSkills (report Tabel 9.15; used by T01 and T20)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.ias import Conn, Principal, current_principal
from app.models import ApiModel

router = APIRouter()


class Skill(ApiModel):
    skill_id: str
    label: str
    aliases: list[str]


class SkillList(ApiModel):
    items: list[Skill]
    total: int


def _like_pattern(query: str) -> str:
    escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


@router.get("/skills", response_model=SkillList, tags=["SCS"])
def list_skills(
    _: Annotated[Principal, Depends(current_principal)],
    conn: Conn,
    query: Annotated[str, Query(max_length=100)] = "",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> SkillList:
    """API-08: any signed-in role reads the catalog, filtered by label or alias (case-insensitive)."""
    where = "label ILIKE %(p)s OR EXISTS (SELECT 1 FROM unnest(aliases) AS alias WHERE alias ILIKE %(p)s)"
    params = {"p": _like_pattern(query), "limit": limit, "offset": offset}
    total = conn.execute(f"SELECT count(*) AS n FROM skills WHERE {where}", params).fetchone()  # type: ignore[arg-type]
    rows = conn.execute(
        f"SELECT skill_id, label, aliases FROM skills WHERE {where}"  # type: ignore[arg-type]
        " ORDER BY skill_id LIMIT %(limit)s OFFSET %(offset)s",
        params,
    ).fetchall()
    return SkillList(items=[Skill(**row) for row in rows], total=total["n"] if total else 0)
