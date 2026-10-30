extends SceneTree
## Measures docs/prediksi/prediksi-euler-rig.md on my arm rig (my_arm_rig.gd): the shoulder
## (bone_0) is turned in 3D, once through Node3D.rotation (Godot's default intrinsic YXZ)
## and once through Quaternion / slerp. Lines are parsed by Source/godot_check.py.
## Run: $GODOT --headless --path godot_project --script res://tools/cek_euler_rig.gd

const FRAMES := 120   # A -> B in 120 equal steps

var _done := false
var _rig: Node3D
var _euler := Node3D.new()   # only used to turn Euler angles into a Basis, Godot's own way


func _process(_delta: float) -> bool:
	if _done:
		return true
	_done = true
	_rig = Node3D.new()
	_rig.set_script(load("res://scripts/my_arm_rig.gd"))
	root.add_child(_rig)
	var rest: Quaternion = _rig.skeleton.get_bone_pose_rotation(0)
	_lock()
	_interpolate()
	_lift()
	_rig.skeleton.set_bone_pose_rotation(0, rest)  # the rig's own MYARM line is printed after this
	_euler.free()
	return true


## Shoulder orientation from Euler degrees (pitch about x, yaw about y, roll about z).
func euler_quat(pitch: float, yaw: float, roll: float) -> Quaternion:
	_euler.rotation = Vector3(deg_to_rad(pitch), deg_to_rad(yaw), deg_to_rad(roll))
	return _euler.basis.get_rotation_quaternion()


## Rotation angle in degrees along the shorter way: q and -q are the same rotation,
## and Quaternion.get_angle() returns 2 acos(w), which can give the long way (e.g. 240 for 120).
func angle_deg(q: Quaternion) -> float:
	return rad_to_deg(2.0 * acos(minf(1.0, absf(q.w))))


## Elbow and fingertip (skeleton space) with the shoulder at q; the other joints keep their photo angles.
func joints(q: Quaternion) -> Array:
	var skel: Skeleton3D = _rig.skeleton
	skel.set_bone_pose_rotation(0, q)
	return [skel.get_bone_global_pose(1).origin, skel.get_bone_global_pose(3).origin]


func _lock() -> void:
	var ref: Array = joints(euler_quat(90, 20, 10))
	var diff_minus := 0.0
	for p in [[15, 5], [10, 0]]:
		var j: Array = joints(euler_quat(90, p[0], p[1]))
		diff_minus = maxf(diff_minus, maxf(j[0].distance_to(ref[0]), j[1].distance_to(ref[1])))
	var j_plus: Array = joints(euler_quat(90, 10, 20))
	var diff_plus := maxf(j_plus[0].distance_to(ref[0]), j_plus[1].distance_to(ref[1]))
	var max_y := 0.0
	for p in [[0, 0], [37, -50], [120, 45], [-80, 170], [10, 95], [-150, -60]]:
		var dir := euler_quat(90, p[0], p[1]) * Vector3.RIGHT   # upper arm direction
		max_y = maxf(max_y, absf(dir.y))
	print("RIG_LOCK pitch=90 yaw_minus_roll_pairs_max_diff=%.9f yaw_plus_roll_pair_diff=%.6f arm_dir_max_abs_y=%.9f" % [
		diff_minus, diff_plus, max_y])


func _interpolate() -> void:
	var qa := euler_quat(0, 0, 0)
	var qb := euler_quat(90, 0, 90)
	print("RIG_B angle_deg=%.6f get_angle_deg=%.6f" % [angle_deg(qb), rad_to_deg(qb.get_angle())])
	var prev_e := qa
	var prev_s := qa
	var steps_e: Array[float] = []
	var steps_s: Array[float] = []
	for k in range(1, FRAMES + 1):
		var t := float(k) / FRAMES
		var qe := euler_quat(90 * t, 0, 90 * t)      # blend the Euler angles linearly
		var qs := qa.slerp(qb, t)
		steps_e.append(angle_deg(prev_e.inverse() * qe))
		steps_s.append(angle_deg(prev_s.inverse() * qs))
		prev_e = qe
		prev_s = qs
		if k % 30 == 0:
			print("RIG_INTERP t=%.4f euler_angle=%.6f slerp_angle=%.6f between=%.6f" % [t,
				angle_deg(qa.inverse() * qe), angle_deg(qa.inverse() * qs), angle_deg(qs.inverse() * qe)])
	var total_e := 0.0
	var total_s := 0.0
	for k in FRAMES:
		total_e += steps_e[k]
		total_s += steps_s[k]
	print("RIG_STEPS frames=%d euler_first_step_speed=%.6f euler_min=%.6f euler_max=%.6f slerp_min=%.6f slerp_max=%.6f" % [
		FRAMES, steps_e[0] * FRAMES, steps_e.min(), steps_e.max(), steps_s.min(), steps_s.max()])
	print("RIG_PATH euler_path_deg=%.6f slerp_path_deg=%.6f net_angle_deg=%.6f" % [total_e, total_s, angle_deg(qa.inverse() * qb)])


func _lift() -> void:
	var qb := euler_quat(90, 0, 90)
	var dir_b := qb * Vector3.RIGHT
	var lifted := Quaternion(Vector3.RIGHT, deg_to_rad(10.0)) * qb
	var dir := lifted * Vector3.RIGHT
	print("RIG_LIFT dir_b=%.6f,%.6f,%.6f dir_after=%.6f,%.6f,%.6f" % [dir_b.x, dir_b.y, dir_b.z, dir.x, dir.y, dir.z])
