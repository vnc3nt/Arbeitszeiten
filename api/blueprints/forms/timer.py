from flask import Blueprint, request, redirect

from web_util.timer import timer_begin, timer_pause, timer_remove_first

timer = Blueprint("timer", __name__, url_prefix="/timer")


@timer.route("/begin", methods=["POST"])
def begin():
    timer_begin()
    return redirect(request.referrer)


@timer.route("/pause", methods=["POST"])
def pause():
    timer_pause()
    return redirect(request.referrer)


@timer.route("/skip", methods=["POST"])
def skip():
    timer_remove_first()
    return redirect(request.referrer)
