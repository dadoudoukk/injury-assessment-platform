"""省市区归一化：兼容直辖市「市辖区」（后台级联）与「北京市/上海市…」（微信 region picker）等等价位写法。"""

from __future__ import annotations

from typing import FrozenSet, Tuple

# 直辖市省级名称
MUNICIPALITIES: FrozenSet[str] = frozenset({"北京市", "上海市", "天津市", "重庆市"})


def _strip(value: str) -> str:
    return (value or "").strip()


def is_municipality(province: str) -> bool:
    return _strip(province) in MUNICIPALITIES


def normalize_region(province: str, city: str, district: str) -> Tuple[str, str, str]:
    """入库用：直辖市市级统一为「市辖区」。"""
    p, c, d = _strip(province), _strip(city), _strip(district)
    if is_municipality(p) and c in (p, "市辖区"):
        c = "市辖区"
    return p, c, d


def city_equivalent_values(province: str, city: str) -> Tuple[str, ...]:
    """匹配用：返回与给定 city 等价的市级名称（含自身），用于 SQL IN 查询。"""
    p, c = _strip(province), _strip(city)
    if not c:
        return ()
    if not is_municipality(p):
        return (c,)
    variants = {c, p, "市辖区"}
    return tuple(v for v in variants if v)
