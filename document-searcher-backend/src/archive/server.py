from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flasgger import Swagger
import api.sources as api_sources
import api.topics as api_topics
import modules.sources as sources
import logging
import re

app = Flask(__name__)
CORS(app)
Swagger(app)

RESERVED_TABLES = ["sources", "topics", "manifests"]

@app.route("/sharepoint-hook", methods=["GET", "POST"])
def sharepoint_hook():
    if "validationToken" in request.args:
        token = request.args["validationToken"]
        return Response(token, status=200, mimetype="text/plain")

    # Handle notifications
    try:
        data = request.get_json(force=True)
        logging.info(f"Incoming notification from Microsoft Graph: {data}")
        #sequences.start_sharepoint_sequence()
    except Exception as e:
        logging.error(f"Failed to parse request body: {e}")
        return jsonify({"error": "Invalid request"}), 400

    return jsonify({"status": "received"}), 202


####################
# Topics endpoints #
####################
@app.route("/list-topics", methods=["GET"])
def list_topics():
    return api_topics.list_topics()
    

@app.route("/create-topic", methods=["POST"])
def create_topic():
    data = request.get_json()
    topic_name = data.get("topic_name", None)
    if topic_name is not None:
        topic_name = re.sub(r'[^a-z0-9_]', '_', topic_name)
        if topic_name.lower() in RESERVED_TABLES:
            return {"status": "error", "message": f"'{topic_name}' is a reserved name"}, 400
        status = api_topics.create_topic(topic_name)
        if status:
            return {"status": "success", "message" : f"Topic '{topic_name}' created successfully"}, 200
        else:
            return {"status": "error", "message" : "The topic already exists"}, 500
    else:
        return {"status": "error", "message" : "Missing parameter: topic_name not specified"}, 400

@app.route("/rename-topic", methods=["PATCH"])
def rename_topic():
    data = request.get_json()
    old_name = data.get("old_name", None)
    new_name = data.get("new_name", None)
    if old_name and new_name:
        status = api_topics.rename_topic(old_name, new_name)
        if status:
            return {"status": "success", "message" : f"Topic rename from '{old_name}' to '{new_name}' successfully"}, 200
        else:
            return {"status": "error", "message" : f"Could not find topic with the name '{old_name}'"}, 500
    else:
        return {"status": "error", "message" : "Missing parameter(s): old_name and/or new_name not specified"}, 400
    

@app.route("/delete-topic", methods=["DELETE"])
def delete_topic():
    data = request.get_json()
    topic_name = data.get("topic_name", None)
    if topic_name is not None:
        status = api_topics.delete_topic(topic_name)
        if status:
            return {"status": "success", "message" : "Topic deleted successfully"}, 200
        else:
            return {"status": "error", "message" : f"Could not find topic with the name '{topic_name}'"}, 500
    else:
        return {"status": "error", "message" : "Missing parameter: topic_name not specified"}, 400

########################
# Sharepoint endpoints #
########################
@app.route("/list-sources", methods=["GET"])
def list_sources():
    topic = request.args.get("topic")

    result = api_sources.list_sources(topic)

    return jsonify(result), 200

@app.route("/add-source", methods=["POST"])
def add_source():
    data = request.get_json()
    topic = data["topic"]
    site = data.get("site", "Sharepoint")
    sources = data["sources"]
    values = [
        (
            topic,
            s["name"],
            f"{s['sharepoint_site']},{s['sharepoint_list']},{s['sharepoint_item']}",
            "0100", # Default 1 AM
            site,
        )
        for s in sources
    ]
    api_sources.add_sources(values)

    return jsonify(status="success", message=f"{len(values)} source(s) added/kept"), 200

@app.route("/remove-source", methods=["DELETE"])
def remove_source():
    data = request.get_json()
    topic_name = data.get("topic_name", None)
    source_id = data.get("source_id", None)
    if topic_name is not None and source_id is not None:
        status = api_sources.remove_source(topic_name, source_id)
        if status:
            return {"status": "success", "message" : "Source removed successfully"}, 200
        else:
            return {"status": "error", "message" : f""}, 500
    else:
        return {"status": "error", "message" : "Missing parameter: topic_name and/or source_id not specified"}, 400
    
@app.route("/update-source", methods=["PATCH"])
def update_source():
    data = request.get_json()
    topic = data.get("topic", None)
    id = data.get("id", None)
    schedule = data.get("schedule", None)
    if topic and id and schedule:
        status = api_sources.update_source(topic, id, schedule)
        if status:
            return {"status": "success", "message" : "Source schedule updated"}, 200
        else:
            return {"status": "error", "message" : f"Could not update source"}, 500
    else:
        return {"status": "error", "message" : "Missing parameter: topic, id and/or schedule not specified"}, 400

########################
# Sharepoint endpoints #
########################
@app.route("/subscribe-sharepoint", methods=["POST"])
def subscribe_sharepoint():
    data = request.get_json()
    token = data.get("token")
    sharepoint_folder = data.get("sharepoint_folder")
    sources.subscribe_to_sharepoint(token, sharepoint_folder)


if __name__ == "__main__":
    app.run(debug=True, port=5000)