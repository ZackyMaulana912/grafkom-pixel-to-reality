extends SceneTree
## Measures the walking Knight (knight_actor.gd with walk = true) at 60 fps.
## For every stance (the same foot stays the lower one) it prints how far that foot
## moved on the floor in world space with root motion, and how far it would have
## moved if the Knight were pushed at a constant speed equal to its average speed.
## Run: $GODOT --headless --path godot_project --script res://tools/cek_knight.gd

const FPS := 60
const SECONDS := 9.0   # the lane is 1.2 m; this stays inside the first leg, before the turn
const SCALE := 0.16

var _done := false


func _process(_delta: float) -> bool:
	if _done:
		return true
	_done = true
	_measure()
	return true


func _measure() -> void:
	var knight: Node3D = load("res://assets/kaykit/Knight.glb").instantiate()
	knight.set_script(load("res://scripts/knight_actor.gd"))
	knight.walk = true
	knight.scale = Vector3.ONE * SCALE
	root.add_child(knight)
	knight.set_process(false)  # driven by hand below, one fixed step per frame
	var anim: Animation = knight.player.get_animation(knight.walk_animation)
	print("KNIGHT clip=%s length=%.6f scale=%.2f" % [knight.walk_animation, anim.length, SCALE])
	var dt := 1.0 / FPS
	var rows := []   # [t, planted foot, foot world pos, foot skeleton-space z, knight z]
	for frame in int(SECONDS * FPS) + 1:
		if frame > 0:
			knight._process(dt)
		var foot: int = knight.planted_foot()
		var pose: Vector3 = knight.skeleton.get_bone_global_pose(foot).origin
		rows.append([frame * dt, foot, knight.skeleton.global_transform * pose, pose.z, knight.position.z])
	var travelled: float = rows[-1][4] - rows[0][4]
	var v: float = travelled / SECONDS
	var worst_rm := 0.0
	var worst_const := 0.0
	var worst_rise := 0.0
	var stances := 0
	var start := 0
	for k in range(1, rows.size() + 1):
		if k < rows.size() and rows[k][1] == rows[start][1]:
			continue
		var end := k - 1
		if start > 0 and k < rows.size() and end > start:  # whole stances only
			var p0: Vector3 = rows[start][2]
			var p1: Vector3 = rows[end][2]
			var slide_rm := Vector2(p1.x - p0.x, p1.z - p0.z).length()
			var y_lo := INF
			var y_hi := -INF
			for q in range(start, end + 1):
				y_lo = minf(y_lo, rows[q][2].y)
				y_hi = maxf(y_hi, rows[q][2].y)
			# same foot motion, but the body pushed at constant v instead of by root motion
			var slide_const: float = (rows[end][3] - rows[start][3]) * SCALE + v * (rows[end][0] - rows[start][0])
			print("STANCE foot=%s t0=%.4f t1=%.4f slide_root_motion=%.9f slide_constant_speed=%.6f rise=%.6f" % [
				knight.skeleton.get_bone_name(rows[start][1]), rows[start][0], rows[end][0], slide_rm, slide_const,
				y_hi - y_lo])
			worst_rm = maxf(worst_rm, slide_rm)
			worst_const = maxf(worst_const, absf(slide_const))
			worst_rise = maxf(worst_rise, y_hi - y_lo)
			stances += 1
		start = k
	print("KNIGHT_WALK stances=%d travelled=%.6f avg_speed=%.6f max_slide_root_motion=%.9f max_slide_constant=%.6f max_rise=%.6f" % [
		stances, travelled, v, worst_rm, worst_const, worst_rise])
	knight.free()
