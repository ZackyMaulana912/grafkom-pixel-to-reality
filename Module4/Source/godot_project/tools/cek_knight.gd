extends SceneTree
## Measures the walking Knight (knight_actor.gd with walk = true) at 60 fps.
## For every stance (the same foot stays the lower one) it prints how far that foot
## moved on the floor in world space with root motion, and how far it would have
## moved if the Knight were pushed at a constant speed equal to its average speed.
## Then it walks a fresh Knight for TURN_SECONDS and, for every 180 deg turn at a lane end,
## adds up how far the planted foot moved on the floor during the turn frames.
## Run: $GODOT --headless --path godot_project --script res://tools/cek_knight.gd

const FPS := 60
const SECONDS := 9.0   # the lane is 1.2 m; this stays inside the first leg, before the turn
const SCALE := 0.16
const TURN_SECONDS := 40.0   # long enough for several turns at both lane ends

var _done := false


func _process(_delta: float) -> bool:
	if _done:
		return true
	_done = true
	_measure()
	_measure_turns()
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


## Per frame: which foot is planted, where it is on the floor before and after the step.
## Summed over the frames that start inside a turn, that is how far the foot was dragged.
func _measure_turns() -> void:
	var knight: Node3D = load("res://assets/kaykit/Knight.glb").instantiate()
	knight.set_script(load("res://scripts/knight_actor.gd"))
	knight.walk = true
	knight.scale = Vector3.ONE * SCALE
	root.add_child(knight)
	knight.set_process(false)
	var dt := 1.0 / FPS
	var lane_x: float = knight.lane_from.x
	var turns := 0
	var drag := 0.0          # foot path on the floor during the current turn
	var worst_turn := 0.0
	var worst_step_turn := 0.0
	var straight := 0.0      # the same sum over the straight frames, for comparison
	var max_lateral := 0.0
	var z_lo := INF
	var z_hi := -INF
	var was_turning := false
	for frame in int(TURN_SECONDS * FPS):
		var turning: bool = knight._turn_left > 0.0
		var foot: int = knight.planted_foot()
		var p0: Vector3 = knight.skeleton.global_transform * knight.skeleton.get_bone_global_pose(foot).origin
		knight._process(dt)
		var p1: Vector3 = knight.skeleton.global_transform * knight.skeleton.get_bone_global_pose(foot).origin
		var step := Vector2(p1.x - p0.x, p1.z - p0.z).length()
		if turning:
			drag += step
			worst_step_turn = maxf(worst_step_turn, step)
		else:
			straight += step
		if was_turning and not turning:
			turns += 1
			print("TURN n=%d end_t=%.4f foot_drag=%.6f at=(%.4f, %.4f)" % [turns, frame * dt, drag,
				knight.position.x, knight.position.z])
			worst_turn = maxf(worst_turn, drag)
			drag = 0.0
		was_turning = turning
		max_lateral = maxf(max_lateral, absf(knight.position.x - lane_x))
		z_lo = minf(z_lo, knight.position.z)
		z_hi = maxf(z_hi, knight.position.z)
	print("KNIGHT_TURN turns=%d max_foot_drag_turn=%.9f max_step_turn=%.9f straight_drag=%.9f max_lateral=%.6f z_range=%.4f..%.4f" % [
		turns, worst_turn, worst_step_turn, straight, max_lateral, z_lo, z_hi])
	knight.free()
