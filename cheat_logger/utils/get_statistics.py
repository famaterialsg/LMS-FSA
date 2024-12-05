from pydantic import PositiveInt, validate_call, BeforeValidator
from typing import Union
from typing_extensions import Annotated
from .fig_generator import gen_fig_counter, gen_fig_face_behavior, gen_fig_tab_behavior


def validate_attempt_type(v: str) -> str:
    from ..views import models_mapping

    if v not in models_mapping:
        raise ValueError(f'Wrong attempt type! Must be one of: {list(models_mapping.keys())}')
    return v


@validate_call
def get_statistics(
    attempt_model_name: Annotated[str, BeforeValidator(validate_attempt_type)],
    attempt_id: Union[PositiveInt, None] = None,
):
    """Get statistics of cheating during exam

    Args:
        attempt_model_name (str): model name of attempt
        attempt_id (Union[PositiveInt, None], optional): attempt id of model name, if None, it will return all attempts in this model. Defaults to None.

    Returns:
        dict: return dict of cheating statistic
    
    Example:
    ```
    >>> attempt_model_name = "StudentAssessmentAttempt"
    >>> attempt_id = 0
    >>> statistics = get_statistics(attempt_model_name, attempt_id)
    {
        0 : {
            "fig_counter_div" : fig_counter_div,
            "fig_tab_behavior_div" : fig_tab_behavior_div,
            "fig_face_behavior_div" : fig_face_behavior_div,
        }
    }
    ```

    In HTML, just simply write for fig of counter
    ```
    <div>
        {{ fig_counter_div|safe }}
    </div>
    ```
    """
    from ..views import models_mapping
    return_data = {}

    if attempt_id is None:
        attempts = models_mapping[attempt_model_name].objects.all()
    else:
        attempts = models_mapping[attempt_model_name].objects.filter(pk=attempt_id)

    for attempt in attempts:
        proctoring_data = attempt.proctoring_data
        duration = attempt.duration
        print(proctoring_data)
        print(duration)
        fig_counter_div = gen_fig_counter(proctoring_data)
        fig_tab_behavior_div = gen_fig_tab_behavior(proctoring_data, duration)
        fig_face_behavior_div = gen_fig_face_behavior(proctoring_data, duration)

        return_data[attempt.id] = {
            "fig_counter_div" : fig_counter_div,
            "fig_tab_behavior_div" : fig_tab_behavior_div,
            "fig_face_behavior_div" : fig_face_behavior_div,
            }
        
    return return_data