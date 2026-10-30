@tool
extends Node3D
## Module 4 -- Euler (gimbal lock) vs Quaternion (slerp) side by side.
## (@tool: the cubes are drawn in the editor too, standing still there.)
##
## Godot's Node3D uses intrinsic YXZ by default (Basis = Ry * Rx * Rz), so its
## MIDDLE axis is x: the lock is at pitch = 90 deg, not at yaw = 90 deg as in
## Source/quaternion.py (Rz * Ry * Rx). At pitch = 90, Ry(yaw) * Rx(90) * Rz(roll)
## = Ry(yaw - roll) * Rx(90), so only yaw - roll is visible. The red cube keeps
## pitch at 90 and swings yaw and roll together with yaw - roll = 10 deg: its
## angles change all the time, but the cube does not move at all. The blue cube
## slerps between two quaternions and turns smoothly.
## (The starter pinned yaw = 90 with pitch - roll fixed, which is not locked in
## this order: docs/catatan/fase5-godot-scene.md, T4.)

const SWING_DEG := 20.0
const YAW_MINUS_ROLL_DEG := 10.0

var _euler_cube: MeshInstance3D
var _quat_cube: MeshInstance3D
var _label: Label3D
var _t := 0.0


func _ready() -> void:
	_euler_cube = _make_cube(Vector3(-2, 1.5, 0), Color(0.9, 0.3, 0.2))
	_quat_cube = _make_cube(Vector3(2, 1.5, 0), Color(0.2, 0.7, 0.9))
	_label = Label3D.new()
	_label.position = Vector3(-2, 0.4, 0)
	_label.pixel_size = 0.006
	add_child(_label)
	_euler_cube.rotation = euler_at(0.0)
	_quat_cube.basis = Basis(quat_at(0.0))
	if not Engine.is_editor_hint():
		_print_check()


func _make_cube(pos: Vector3, color: Color) -> MeshInstance3D:
	var mesh_instance := MeshInstance3D.new()
	mesh_instance.mesh = BoxMesh.new()
	mesh_instance.position = pos
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mesh_instance.material_override = mat
	add_child(mesh_instance)
	return mesh_instance


## Euler angles (radians, Godot's x = pitch, y = yaw, z = roll) of the red cube at time t.
func euler_at(t: float) -> Vector3:
	var roll := SWING_DEG * sin(t)
	var yaw := roll + YAW_MINUS_ROLL_DEG
	return Vector3(deg_to_rad(90.0), deg_to_rad(yaw), deg_to_rad(roll))


## Orientation of the blue cube at time t: slerp between two independent orientations.
func quat_at(t: float) -> Quaternion:
	var q0 := Quaternion(Vector3.UP, 0.0)
	var q1 := Quaternion(Vector3(1, 1, 0).normalized(), deg_to_rad(120.0))
	return q0.slerp(q1, (sin(t) + 1.0) * 0.5)


func _process(delta: float) -> void:
	if Engine.is_editor_hint():
		return  # show the cubes in the editor, but only move them while playing
	_t += delta
	var e := euler_at(_t)
	_euler_cube.rotation = e
	_quat_cube.basis = Basis(quat_at(_t))
	_label.text = "Euler YXZ: pitch %.0f  yaw %.1f  roll %.1f\nyaw - roll = %.1f -> kubus diam" % [
		rad_to_deg(e.x), rad_to_deg(e.y), rad_to_deg(e.z), rad_to_deg(e.y - e.z)]


## Basis of the red cube at a few times, in the format Source/godot_check.py reads,
## plus how far each cube's Basis moved away from its t = 0 Basis over those times.
func _print_check() -> void:
	var probe := Node3D.new()  # same default rotation_order as the cube
	probe.rotation = euler_at(0.0)
	var euler_start := probe.basis
	var quat_start := Basis(quat_at(0.0))
	var euler_moved := 0.0
	var quat_moved := 0.0
	for t in [0.0, 0.5, 1.0, 1.5, 2.0]:
		var e := euler_at(t)
		probe.rotation = e
		var rows := []
		for i in 3:
			for j in 3:
				rows.append("%.9f" % probe.basis[j][i])
		print("BASIS gimbal_demo order=%d deg=%s,%s,%s m=%s" % [probe.rotation_order, rad_to_deg(e.x),
			rad_to_deg(e.y), rad_to_deg(e.z), ",".join(rows)])
		euler_moved = maxf(euler_moved, _max_diff(probe.basis, euler_start))
		quat_moved = maxf(quat_moved, _max_diff(Basis(quat_at(t)), quat_start))
	probe.free()
	print("GIMBAL euler_cube_max_change=%.9f quat_cube_max_change=%.9f" % [euler_moved, quat_moved])


func _max_diff(a: Basis, b: Basis) -> float:
	var m := 0.0
	for j in 3:
		for i in 3:
			m = maxf(m, absf(a[j][i] - b[j][i]))
	return m
