import json
import os
import re
import uuid
from datetime import datetime
from typing import Any, Callable


def _matches(doc: dict, query: dict) -> bool:
    """Very small subset of Mongo's query language: equality, $gt/$gte/$lt/
    $lte/$ne/$in/$regex, plus dotted-path lookups (e.g. 'attributes.color')."""
    for key, cond in query.items():
        value = _get_path(doc, key)
        if isinstance(cond, dict) and any(k.startswith("$") for k in cond):
            for op, operand in cond.items():
                if op == "$gt" and not (value is not None and value > operand):
                    return False
                if op == "$gte" and not (value is not None and value >= operand):
                    return False
                if op == "$lt" and not (value is not None and value < operand):
                    return False
                if op == "$lte" and not (value is not None and value <= operand):
                    return False
                if op == "$ne" and value == operand:
                    return False
                if op == "$in" and value not in operand:
                    return False
                if op == "$regex" and not re.search(operand, str(value or ""), re.IGNORECASE):
                    return False
        else:
            if value != cond:
                return False
    return True


def _get_path(doc: dict, dotted_key: str):
    cur = doc
    for part in dotted_key.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def _set_path(doc: dict, dotted_key: str, value):
    parts = dotted_key.split(".")
    cur = doc
    for part in parts[:-1]:
        cur = cur.setdefault(part, {})
    cur[parts[-1]] = value


class Collection:
    def __init__(self, path: str):
        self.path = path
        self._indexes = []
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump([], f)

    # -- internal I/O --------------------------------------------------
    def _load(self) -> list:
        with open(self.path, "r") as f:
            return json.load(f)

    def _save(self, docs: list):
        with open(self.path, "w") as f:
            json.dump(docs, f, indent=1, default=str)

    # -- CRUD (mirrors pymongo) -----------------------------------------
    def insert_one(self, doc: dict):
        """Mongo equivalent: db.<collection>.insertOne(doc)"""
        docs = self._load()
        doc = dict(doc)
        doc.setdefault("_id", str(uuid.uuid4())[:8])
        docs.append(doc)
        self._save(docs)
        return doc["_id"]

    def insert_many(self, docs_in: list):
        """Mongo equivalent: db.<collection>.insertMany(docs)"""
        docs = self._load()
        ids = []
        for d in docs_in:
            d = dict(d)
            d.setdefault("_id", str(uuid.uuid4())[:8])
            docs.append(d)
            ids.append(d["_id"])
        self._save(docs)
        return ids

    def find(self, query: dict = None, limit: int = None, sort: tuple = None):
        """Mongo equivalent: db.<collection>.find(query).sort(...).limit(...)"""
        query = query or {}
        docs = [d for d in self._load() if _matches(d, query)]
        if sort:
            field, direction = sort
            docs.sort(key=lambda d: (_get_path(d, field) is None, _get_path(d, field)),
                       reverse=(direction == -1))
        if limit:
            docs = docs[:limit]
        return docs

    def find_one(self, query: dict = None):
        """Mongo equivalent: db.<collection>.findOne(query)"""
        results = self.find(query, limit=1)
        return results[0] if results else None

    def update_one(self, query: dict, update: dict):
        """Mongo equivalent: db.<collection>.updateOne(query, update)"""
        docs = self._load()
        for d in docs:
            if _matches(d, query):
                self._apply_update(d, update)
                self._save(docs)
                return 1
        return 0

    def update_many(self, query: dict, update: dict):
        """Mongo equivalent: db.<collection>.updateMany(query, update)"""
        docs = self._load()
        count = 0
        for d in docs:
            if _matches(d, query):
                self._apply_update(d, update)
                count += 1
        self._save(docs)
        return count

    @staticmethod
    def _apply_update(d: dict, update: dict):
        if "$set" in update:
            for k, v in update["$set"].items():
                _set_path(d, k, v)
        if "$inc" in update:
            for k, v in update["$inc"].items():
                _set_path(d, k, (_get_path(d, k) or 0) + v)
        if "$push" in update:
            for k, v in update["$push"].items():
                d.setdefault(k, [])
                if isinstance(d[k], list):
                    d[k].append(v)

    def delete_one(self, query: dict):
        """Mongo equivalent: db.<collection>.deleteOne(query)"""
        docs = self._load()
        for i, d in enumerate(docs):
            if _matches(d, query):
                docs.pop(i)
                self._save(docs)
                return 1
        return 0

    def delete_many(self, query: dict):
        """Mongo equivalent: db.<collection>.deleteMany(query)"""
        docs = self._load()
        keep = [d for d in docs if not _matches(d, query)]
        removed = len(docs) - len(keep)
        self._save(keep)
        return removed

    def count_documents(self, query: dict = None):
        """Mongo equivalent: db.<collection>.countDocuments(query)"""
        return len(self.find(query or {}))

    def create_index(self, field: str):
        """Mongo equivalent: db.<collection>.createIndex({field: 1})
        (Recorded only -- this teaching engine scans linearly; a real
        MongoDB deployment uses this call to build a B-tree index.)"""
        self._indexes.append(field)

    # -- a small but real aggregation pipeline ---------------------------
    def aggregate(self, pipeline: list):
        """Mongo equivalent: db.<collection>.aggregate([...])
        Supports the subset of stages used in this project:
        $match, $group (with $sum/$avg/$min/$max/$push), $sort, $limit,
        $project, $lookup (manual local join)."""
        docs = self._load()
        for stage in pipeline:
            if "$match" in stage:
                docs = [d for d in docs if _matches(d, stage["$match"])]
            elif "$sort" in stage:
                for field, direction in reversed(list(stage["$sort"].items())):
                    docs.sort(key=lambda d: (_get_path(d, field) is None, _get_path(d, field)),
                               reverse=(direction == -1))
            elif "$limit" in stage:
                docs = docs[: stage["$limit"]]
            elif "$project" in stage:
                proj = stage["$project"]
                docs = [{k: _get_path(d, k) for k in proj if proj[k]} for d in docs]
            elif "$group" in stage:
                docs = self._group(docs, stage["$group"])
            elif "$lookup" in stage:
                docs = self._lookup(docs, stage["$lookup"])
            elif "$unwind" in stage:
                field = stage["$unwind"].lstrip("$")
                out = []
                for d in docs:
                    vals = _get_path(d, field)
                    if isinstance(vals, list):
                        for v in vals:
                            nd = dict(d)
                            _set_path(nd, field, v)
                            out.append(nd)
                    else:
                        out.append(d)
                docs = out
        return docs

    @staticmethod
    def _group(docs, spec):
        groups: dict[Any, list] = {}
        id_expr = spec["_id"]
        for d in docs:
            if isinstance(id_expr, str) and id_expr.startswith("$"):
                key = _get_path(d, id_expr[1:])
            else:
                key = id_expr
            groups.setdefault(key, []).append(d)
        out = []
        for key, items in groups.items():
            row = {"_id": key}
            for field, agg in spec.items():
                if field == "_id":
                    continue
                op, arg = list(agg.items())[0]
                arg_field = arg.lstrip("$") if isinstance(arg, str) else None
                values = [_get_path(d, arg_field) for d in items] if arg_field else [1 for _ in items]
                values = [v for v in values if v is not None]
                if op == "$sum":
                    row[field] = sum(values) if arg_field else len(items)
                elif op == "$avg":
                    row[field] = round(sum(values) / len(values), 2) if values else 0
                elif op == "$min":
                    row[field] = min(values) if values else None
                elif op == "$max":
                    row[field] = max(values) if values else None
                elif op == "$push":
                    row[field] = values
            out.append(row)
        return out

    def _lookup(self, docs, spec):
        from_col = Collection(os.path.join(os.path.dirname(self.path), f"{spec['from']}.json"))
        foreign_docs = from_col._load()
        local_f, foreign_f, as_f = spec["localField"], spec["foreignField"], spec["as"]
        index = {}
        for fd in foreign_docs:
            index.setdefault(_get_path(fd, foreign_f), []).append(fd)
        out = []
        for d in docs:
            nd = dict(d)
            nd[as_f] = index.get(_get_path(d, local_f), [])
            out.append(nd)
        return out


class DocumentDB:
    """Mongo equivalent: db = client['ecommerce_nosql']"""
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
        self._collections = {}

    def __getitem__(self, name: str) -> Collection:
        if name not in self._collections:
            self._collections[name] = Collection(os.path.join(self.base_dir, f"{name}.json"))
        return self._collections[name]

    def collection_names(self):
        return [f[:-5] for f in os.listdir(self.base_dir) if f.endswith(".json")]
