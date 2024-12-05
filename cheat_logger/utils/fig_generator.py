import plotly.graph_objects as go


def gen_fig_counter(proctoring_data):
    proctoring_counter = {
        behavior_key: len(behavior_value)
        for behavior_key, behavior_value in proctoring_data.items()
    }
    proctoring_counter_fig = go.Figure(
        data=[
            go.Bar(
                x=list(proctoring_counter.keys()), y=list(proctoring_counter.values())
            )
        ]
    )
    proctoring_counter_fig.update_layout(
        title={"text": "Counter", "x": 0.5, "xanchor": "center"},
        xaxis_title="Behavior",
        yaxis_title="Freqs",
    )
    proctoring_counter_div = proctoring_counter_fig.to_html(full_html=False)

    return proctoring_counter_div


def gen_fig_tab_behavior(proctoring_data, duration):
    time_start = None
    tab_behavior = {}
    last_behavior = None
    behavior_types = set()
    for _, data in proctoring_data.get("tab_behavior", {}).items():
        behavior = data.get("behavior", "")
        time = data.get("time", 0)
        behavior_types.add(behavior)

        if last_behavior is None:
            last_behavior = behavior
            time_start = time
            continue

        if behavior is last_behavior:
            continue
        else:
            tab_behavior[last_behavior] = tab_behavior.get(last_behavior, 0) + (time - time_start) / 1000
            last_behavior = behavior
            time_start = time

    total_behavior_time = 0

    for behavior_type in behavior_types:
        total_behavior_time += tab_behavior.get(behavior_type, 0)

    tab_behavior[last_behavior] = tab_behavior.get(last_behavior, 0) + (duration - total_behavior_time)

    tab_behavior_fig = go.Figure(
        data=[
            go.Pie(labels=list(tab_behavior.keys()), values=list(tab_behavior.values()))
        ]
    )
    tab_behavior_fig.update_layout(
        title={"text": "Tab behavior", "x": 0.5, "xanchor": "center"},
    )
    tab_behavior_div = tab_behavior_fig.to_html(
        full_html=False, config={"responsive": True}
    )

    return tab_behavior_div


def gen_fig_face_behavior(proctoring_data, duration):
    face_behavior = {}
    time_start = None
    last_num_faces = None
    last_face_behavior = None

    for _, data in proctoring_data.get("face_behavior", {}).items():
        if data.get("code", "200") == "404":
            continue

        time = data.get("time", 0)
        num_faces = len([key for key, value in data.items() if key.startswith("face_")])

        if num_faces == 0:
            behavior = "no_face"
        elif num_faces == 1:
            behavior = data.get("face_0", "")
        else:
            behavior = f"{num_faces}_faces"

        if (last_num_faces == num_faces) and (last_face_behavior == behavior):
            continue

        if time_start is not None:
            face_behavior[last_face_behavior] = face_behavior.get(
                last_face_behavior, 0
            ) + (time - time_start)
            
        time_start = time
        last_face_behavior = behavior
        last_num_faces = num_faces
        
    if len(face_behavior) == 0:
        return '<h4 class="text-center">No Face Behavior Recoded!</h4>'

    face_behavior = {key: round(value, 2) for key, value in face_behavior.items()}
    face_behavior = dict(sorted(face_behavior.items(), key=lambda item: item[0]))

    other_behavior_time = sum(
        [value for key, value in face_behavior.items() if key is not last_face_behavior]
    )


    face_behavior[last_face_behavior] = (
        face_behavior.get(last_face_behavior, 0) + duration - other_behavior_time
    )
    face_behavior_fig = go.Figure(
        data=[
            go.Pie(
                labels=list(face_behavior.keys()), values=list(face_behavior.values())
            )
        ]
    )
    face_behavior_fig.update_layout(
        title={"text": "Face behavior", "x": 0.5, "xanchor": "center"},
    )
    face_behavior_div = face_behavior_fig.to_html(
        full_html=False, config={"responsive": True}
    )

    return face_behavior_div