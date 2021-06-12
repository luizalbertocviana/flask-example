from typing import List
from flask import Flask, request
import requests

app = Flask(__name__)

cache = dict()
def query_target_api(tag: str) -> dict:
    if tag not in cache:
        # I should not make public the actual url
        target_url =  "https://secret-url/blog/posts?tag=%s" % tag

        response = requests.get(target_url).json()
        posts = response['posts']

        cache[tag] = {post["id"] : post for post in posts}

    return cache[tag]

@app.route("/api/ping")
def ping():
    return {"success": True}, 200

def union_two_dicts(dict_a: dict, dict_b: dict) -> dict:
    key_set_a = set(dict_a.keys())
    key_set_b = set(dict_b.keys())
    keys_from_b = key_set_b.difference(key_set_a)

    result = dict(dict_a)
    for key_b in keys_from_b:
        result[key_b] = dict_b[key_b]

    return result

def union_dict_list(dicts: List[dict]) -> dict:
    n = len(dicts)

    if n == 0:
        return dict()
    elif n == 1:
        return dicts[0]
    else:
        half_n = int(n / 2)
        first_half = dicts[:half_n]
        second_half = dicts[half_n:]

        union_first_half = union_dict_list(first_half)
        union_second_half = union_dict_list(second_half)

        return union_two_dicts(union_first_half, union_second_half)

@app.route("/api/posts")
def posts():
    tags = request.args.get("tags")

    if tags is None:
        return {"error": "Tags parameter is required"}, 400
    else:
        sorting_key = request.args.get("sortBy")
        direction = request.args.get("direction")

        return resolve_posts_route(tags, sorting_key, direction)

def resolve_posts_route(tags, sorting_key, direction):
    if sorting_key is None:
        sorting_key = "id"
    if direction is None:
        direction = "asc"

    if sorting_key not in ["id", "likes", "reads", "popularity"]:
        return {"error": "sortBy parameter is invalid"}, 400
    if direction not in ["asc", "desc"]:
        return {"error": "direction parameter is invalid"}, 400

    tag_list = tags.split(',')
    posts_dict_list = [query_target_api(tag) for tag in tag_list]
    union_posts_dict = union_dict_list(posts_dict_list)

    result_posts = list(union_posts_dict.values())

    result_posts.sort(key     = lambda post: post[sorting_key],
                      reverse = direction == "desc")

    return {"posts": result_posts}, 200
