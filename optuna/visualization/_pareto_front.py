import json
from typing import Any
from typing import List
from typing import Optional

import optuna
from optuna._experimental import experimental
from optuna.study import Study
from optuna.trial import FrozenTrial
from optuna.trial import TrialState
from optuna.visualization._plotly_imports import _imports


if _imports.is_successful():
    from optuna.visualization._plotly_imports import go

_logger = optuna.logging.get_logger(__name__)


@experimental("2.4.0")
def plot_pareto_front(
    study: Study,
    *,
    target_names: Optional[List[str]] = None,
    include_dominated_trials: bool = True,
    axis_order: Optional[List[int]] = None,
) -> "go.Figure":
    """Plot the Pareto front of a study.

    Example:

        The following code snippet shows how to plot the Pareto front of a study.

        .. plotly::

            import optuna


            def objective(trial):
                x = trial.suggest_float("x", 0, 5)
                y = trial.suggest_float("y", 0, 3)

                v0 = 4 * x ** 2 + 4 * y ** 2
                v1 = (x - 5) ** 2 + (y - 5) ** 2
                return v0, v1


            study = optuna.create_study(directions=["minimize", "minimize"])
            study.optimize(objective, n_trials=50)

            fig = optuna.visualization.plot_pareto_front(study)
            fig.show()

    Args:
        study:
            A :class:`~optuna.study.Study` object whose trials are plotted for their objective
            values.
        target_names:
            Objective name list used as the axis titles. If :obj:`None` is specified,
            "Objective {objective_index}" is used instead.
        include_dominated_trials:
            A flag to include all dominated trial's objective values.
        axis_order:
            A list of indices indicating the axis order. If :obj:`None` is specified,
            default order is used.

    Returns:
        A :class:`plotly.graph_objs.Figure` object.

    Raises:
        :exc:`ValueError`:
            If the number of objectives of ``study`` isn't 2 or 3.
    """

    _imports.check()

    if len(study.directions) == 2:
        return _get_pareto_front_2d(study, target_names, include_dominated_trials, axis_order)
    elif len(study.directions) == 3:
        return _get_pareto_front_3d(study, target_names, include_dominated_trials, axis_order)
    else:
        raise ValueError("`plot_pareto_front` function only supports 2 or 3 objective studies.")


def _get_non_pareto_front_trials(
    study: Study, pareto_trials: List[FrozenTrial]
) -> List[FrozenTrial]:

    non_pareto_trials = []
    for trial in study.get_trials():
        if trial.state == TrialState.COMPLETE and trial not in pareto_trials:
            non_pareto_trials.append(trial)
    return non_pareto_trials


def _get_pareto_front_2d(
    study: Study,
    target_names: Optional[List[str]],
    include_dominated_trials: bool = False,
    axis_order: Optional[List[int]] = None,
) -> "go.Figure":
    if target_names is None:
        target_names = ["Objective 0", "Objective 1"]
    elif len(target_names) != 2:
        raise ValueError("The length of `target_names` is supposed to be 2.")

    trials = study.best_trials
    n_best_trials = len(trials)
    if len(trials) == 0:
        _logger.warning("Your study does not have any completed trials.")

    if include_dominated_trials:
        non_pareto_trials = _get_non_pareto_front_trials(study, trials)
        trials += non_pareto_trials

    if axis_order is None:
        axis_order = list(range(2))
    else:
        if len(axis_order) != 2:
            raise ValueError(
                f"Size of `axis_order` {axis_order}. Expect: 2, Actual: {len(axis_order)}."
            )
        if len(set(axis_order)) != 2:
            raise ValueError(f"Elements of given `axis_order` {axis_order} are not unique!")
        if max(axis_order) > 1:
            raise ValueError(
                f"Given `axis_order` {axis_order} contains invalid index {max(axis_order)} "
                "higher than 1."
            )
        if min(axis_order) < 0:
            raise ValueError(
                f"Given `axis_order` {axis_order} contains invalid index {min(axis_order)} "
                "lower than 0."
            )

    data = [
        go.Scatter(
            x=[t.values[axis_order[0]] for t in trials[n_best_trials:]],
            y=[t.values[axis_order[1]] for t in trials[n_best_trials:]],
            text=[_make_hovertext(t) for t in trials[n_best_trials:]],
            mode="markers",
            hovertemplate="%{text}<extra>Trial</extra>",
            marker={
                "line": {"width": 0.5, "color": "Grey"},
                "color": [t.number for t in trials[n_best_trials:]],
                "colorscale": "Blues",
                "colorbar": {
                    "title": "#Trials",
                },
            },
            showlegend=False,
        ),
        go.Scatter(
            x=[t.values[axis_order[0]] for t in trials[:n_best_trials]],
            y=[t.values[axis_order[1]] for t in trials[:n_best_trials]],
            text=[_make_hovertext(t) for t in trials[:n_best_trials]],
            mode="markers",
            hovertemplate="%{text}<extra>Best Trial</extra>",
            marker={
                "line": {"width": 0.5, "color": "Grey"},
                "color": [t.number for t in trials[:n_best_trials]],
                "colorscale": "Reds",
                "colorbar": {
                    "title": "#Best trials",
                    "x": 1.1 if include_dominated_trials else 1,
                    "xpad": 40,
                },
            },
            showlegend=False,
        ),
    ]
    layout = go.Layout(
        title="Pareto-front Plot",
        xaxis_title=target_names[axis_order[0]],
        yaxis_title=target_names[axis_order[1]],
    )
    return go.Figure(data=data, layout=layout)


def _get_pareto_front_3d(
    study: Study,
    target_names: Optional[List[str]],
    include_dominated_trials: bool = False,
    axis_order: Optional[List[int]] = None,
) -> "go.Figure":
    if target_names is None:
        target_names = ["Objective 0", "Objective 1", "Objective 2"]
    elif len(target_names) != 3:
        raise ValueError("The length of `target_names` is supposed to be 3.")

    trials = study.best_trials
    n_best_trials = len(trials)
    if len(trials) == 0:
        _logger.warning("Your study does not have any completed trials.")

    if include_dominated_trials:
        non_pareto_trials = _get_non_pareto_front_trials(study, trials)
        trials += non_pareto_trials

    if axis_order is None:
        axis_order = list(range(3))
    else:
        if len(axis_order) != 3:
            raise ValueError(
                f"Size of `axis_order` {axis_order}. Expect: 3, Actual: {len(axis_order)}."
            )
        if len(set(axis_order)) != 3:
            raise ValueError(f"Elements of given `axis_order` {axis_order} are not unique!.")
        if max(axis_order) > 2:
            raise ValueError(
                f"Given `axis_order` {axis_order} contains invalid index {max(axis_order)} "
                "higher than 2."
            )
        if min(axis_order) < 0:
            raise ValueError(
                f"Given `axis_order` {axis_order} contains invalid index {min(axis_order)} "
                "lower than 0."
            )

    data = [
        go.Scatter3d(
            x=[t.values[axis_order[0]] for t in trials[n_best_trials:]],
            y=[t.values[axis_order[1]] for t in trials[n_best_trials:]],
            z=[t.values[axis_order[2]] for t in trials[n_best_trials:]],
            text=[_make_hovertext(t) for t in trials[n_best_trials:]],
            hovertemplate="%{text}<extra>Trial</extra>",
            mode="markers",
            marker={
                "line": {"width": 0.5, "color": "Grey"},
                "color": [t.number for t in trials[n_best_trials:]],
                "colorscale": "Blues",
                "colorbar": {
                    "title": "#Trials",
                },
            },
            showlegend=False,
        ),
        go.Scatter3d(
            x=[t.values[axis_order[0]] for t in trials[:n_best_trials]],
            y=[t.values[axis_order[1]] for t in trials[:n_best_trials]],
            z=[t.values[axis_order[2]] for t in trials[:n_best_trials]],
            text=[_make_hovertext(t) for t in trials[:n_best_trials]],
            hovertemplate="%{text}<extra>Best Trial</extra>",
            mode="markers",
            marker={
                "line": {"width": 0.5, "color": "Grey"},
                "color": [t.number for t in trials[:n_best_trials]],
                "colorscale": "Reds",
                "colorbar": {
                    "title": "#Best trials",
                    "x": 1.1 if include_dominated_trials else 1,
                    "xpad": 40,
                },
            },
            showlegend=False,
        ),
    ]
    layout = go.Layout(
        title="Pareto-front Plot",
        scene={
            "xaxis_title": target_names[axis_order[0]],
            "yaxis_title": target_names[axis_order[1]],
            "zaxis_title": target_names[axis_order[2]],
        },
    )
    return go.Figure(data=data, layout=layout)


def _make_json_compatible(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except TypeError:
        # the value can't be converted to JSON directly, so return a string representation
        return str(value)


def _make_hovertext(trial: FrozenTrial) -> str:
    user_attrs = {key: _make_json_compatible(value) for key, value in trial.user_attrs.items()}
    user_attrs_dict = {"user_attrs": user_attrs} if user_attrs else {}
    text = json.dumps(
        {
            "number": trial.number,
            "values": trial.values,
            "params": trial.params,
            **user_attrs_dict,
        },
        indent=2,
    )
    return text.replace("\n", "<br>")
