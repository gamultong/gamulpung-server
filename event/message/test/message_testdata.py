FETCH_TILES_EXAMPLE = \
    """
{
	"event": "fetch-tiles",
	"payload": {
		"start_p": {
			"x": 0,
			"y": 0
        },
        "end_p": {
			"x": 0,
			"y": 0
        }
	}
}
"""

TILES_EXAMPLE = \
    """
{
	"event": "tiles",
	"payload": {
		"start_p": {
			"x": 0,
			"y": 0
        },
        "end_p": {
			"x": 4,
			"y": 4
        },
		"tiles": "CCCCCCCCCCC111CC1F1CC111C"
	}
}
"""

INVALID_EVENT_EXAMPLE = \
    """
{
	"event": "ayo invalid",
	"payload": {
		"foo": "bar"
	}
}
"""
