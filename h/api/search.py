"""The h API search functions.

All search (Annotation.search(), Annotation.search_raw()) and Elasticsearch
stuff should be encapsulated in this module.

"""
import logging

import webob.multidict

from h.api.models import Annotation

log = logging.getLogger(__name__)


def build_query(request_params, user_id=None):
    """Return an Elasticsearch query dict for the given h search API params.

    Translates the HTTP request params accepted by the h search API into an
    Elasticsearch query dict.

    :param request_params: the HTTP request params that were posted to the
        h search API
    :type request_params: webob.multidict.NestedMultiDict

    :param user_id: the ID of the authorized user (optional, default: None),
        if a user_id is given then this user's annotations will never be
        filtered out even if they have a NIPSA flag
    :type user_id: unicode or None

    :returns: an Elasticsearch query dict corresponding to the given h search
        API params
    :rtype: dict

    """
    # NestedMultiDict objects are read-only, so we need to copy to make it
    # modifiable.
    request_params = request_params.copy()

    try:
        from_ = int(request_params.pop("offset"))
        if from_ < 0:
            raise ValueError
    except (ValueError, KeyError):
        from_ = 0

    try:
        size = int(request_params.pop("limit"))
        if size < 0:
            raise ValueError
    except (ValueError, KeyError):
        size = 20

    query = {
        "from": from_,
        "size": size,
        "sort": [
            {
                request_params.pop("sort", "updated"): {
                    "ignore_unmapped": True,
                    "order": request_params.pop("order", "desc")
                }
            }
        ]
    }

    matches = []
    if "any" in request_params:
        matches.append({
            "multi_match": {
                "fields": ["quote", "tags", "text", "uri.parts", "user"],
                "query": request_params.getall("any"),
                "type": "cross_fields"
            }
        })
        del request_params["any"]

    for key, value in request_params.items():
        matches.append({"match": {key: value}})
    matches = matches or [{"match_all": {}}]

    # If any one of these "should" clauses is true then the annotation will
    # get through the filter.
    should_clauses = [{"not": {"term": {"not_in_public_site_areas": True}}}]

    if user_id:
        # Always show the logged-in user's annotations even if they have nipsa.
        should_clauses.append({"term": {"user": user_id}})

    # Filter out NIPSA'd annotations.
    query["query"] = {
        "filtered": {
            "filter": {"bool": {"should": should_clauses}},
            "query": {"bool": {"must": matches}}
        }
    }

    return query


def search(request_params, user=None):
    """Search with the given params and return the matching annotations.

    :param request_params: the HTTP request params that were posted to the
        h search API
    :type request_params: webob.multidict.NestedMultiDict

    :param user: the authorized user, or None
    :type user: h.accounts.models.User or None

    :returns: a dict with keys "rows" (the list of matching annotations, as
        dicts) and "total" (the number of matching annotations, an int)
    :rtype: dict

    """
    user_id = user.id if user else None
    log.debug("Searching with user=%s, for uri=%s",
              str(user_id), request_params.get('uri'))

    query = build_query(request_params, user_id)
    results = Annotation.search_raw(query, user=user)
    count = Annotation.search_raw(query, {'search_type': 'count'},
                                  raw_result=True)
    return {"rows": results, "total": count["hits"]["total"]}


def index(user=None):
    """Return the 20 most recent annotations, most-recent first.

    Returns the 20 most recent annotations that are visible to the given user,
    or that are public if user is None.

    """
    return search(webob.multidict.NestedMultiDict({"limit": 20}), user=user)