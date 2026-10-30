extends SceneTree
## Measures where the stick figure's feet really are while they are planted (T11).
## Runs foot_slide_demo.gd frame by frame at 60 fps for several root speeds and prints,
## for every stance, how far that foot moved in world space while it should have been
## planted, and the footfall marker position the script computes from its formula.
## A stance is what the animation itself defines: the leg whose knee is straight
## (_pose bends a knee only while max(0, cos(leg_phase)) > 0, i.e. while it swings).
## Run: $GODOT --headless --path godot_project --script res://tools/cek_walker.gd

const FPS := 60
const SECONDS := 4.0
# 1.5 = starter "buggy", 1.0 = starter "fixed" (stride_per_cycle x cycle_rate),
# 1.601 = what the leg geometry covers per cycle: 2 stances x 2 x 0.92 m x sin(0.45 rad)
const SPEEDS := [1.5, 1.0, 1.601]

var _done := false


func _process(_delta: float) -> bool:
	if _done:
		return true
	_done = true
	for speed in SPEEDS:
		_measure(speed)
	return true


func _measure(speed: float) -> void:
	var walker: Node3D = load("res://scripts/foot_slide_demo.gd").new()
	walker.scripted_speed = speed
	walker.loop_seconds = 1000.0
	root.add_child(walker)
	walker.set_process(false)  # driven by hand below, one fixed step per frame
	walker._next_footfall_t = INF  # no marker nodes; the marker position is computed below
	var feet: Array[Node3D] = []
	for knee in walker._knees:
		for c in knee.get_children():
			if c is MeshInstance3D and c.mesh is BoxMesh:
				feet.append(c)
	var dt := 1.0 / FPS
	var track := [[], []]   # per foot: [t, x, y, planted]
	for frame in int(SECONDS * FPS) + 1:
		if frame > 0:
			walker._process(dt)
		for i in 2:
			var p := feet[i].global_position
			track[i].append([frame * dt, p.x, p.y, walker._knees[i].rotation.z == 0.0])
	var slides := []
	for i in 2:
		var start := -1
		for k in track[i].size():
			var planted: bool = track[i][k][3]
			if planted and start < 0:
				start = k
			if (not planted or k == track[i].size() - 1) and start >= 0:
				var end: int = k - 1 if not planted else k
				if start > 0 and end < track[i].size() - 1 and end > start:  # only whole stances
					var t0: float = track[i][start][0]
					var x0: float = track[i][start][1]
					var x1: float = track[i][end][1]
					var marker_x: float = walker.stride_per_cycle * walker.cycle_rate * t0
					var y_lo := INF
					var y_hi := -INF
					for q in range(start, end + 1):
						y_lo = minf(y_lo, track[i][q][2])
						y_hi = maxf(y_hi, track[i][q][2])
					print("STANCE speed=%.3f foot=%d t0=%.4f t1=%.4f x0=%.4f x1=%.4f slide=%.4f rise=%.4f marker_x=%.4f marker_off=%.4f" % [
						speed, i, t0, track[i][end][0], x0, x1, x1 - x0, y_hi - y_lo, marker_x, x0 - marker_x])
					slides.append(absf(x1 - x0))
				start = -1
	var worst := 0.0
	for s in slides:
		worst = maxf(worst, s)
	print("WALKER speed=%.3f stances=%d max_abs_slide=%.4f" % [speed, slides.size(), worst])
	walker.free()
