@tool
extends Node3D
## Module 4 -- forward & inverse kinematics for a 2-bone planar arm.
## (@tool: the arm and its IK target are also drawn in the editor.)
## Same convention and formulas as Source/fk.py and ik.py (local angles in
## degrees, theta1 from +x, theta2 from the upper arm), so the numbers printed
## here can be compared with the Python output line by line.
##
## Controls while playing:
##   [Space] toggles the FK pose (shoulder 30 deg, elbow 60 deg) and the IK pose.
##   [U]     moves the IK target out of reach and back, to show the warning.

@export var shoulder_length: float = 3.0
@export var elbow_length: float = 2.0
@export var shoulder_angle_deg: float = 30.0
@export var elbow_angle_deg: float = 60.0
@export var ik_target: Vector3 = Vector3(4, 1, 0)
@export var unreachable_target: Vector3 = Vector3(5.5, 0, 0)

const REACH_COLOR := Color(0.2, 0.85, 0.3)
const NO_REACH_COLOR := Color(0.95, 0.15, 0.15)

var _shoulder_mesh: MeshInstance3D
var _elbow_mesh: MeshInstance3D
var _target_mesh: MeshInstance3D
var _target_mat: StandardMaterial3D
var _label: Label3D
var _use_ik := false
var _target := Vector3.ZERO


func _ready() -> void:
	_shoulder_mesh = _make_bone(shoulder_length, Color(0.2, 0.6, 1.0))
	_elbow_mesh = _make_bone(elbow_length, Color(1.0, 0.6, 0.1))
	add_child(_shoulder_mesh)
	add_child(_elbow_mesh)

	_target_mesh = MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = 0.15
	sphere.height = 0.3
	_target_mesh.mesh = sphere
	_target_mat = StandardMaterial3D.new()
	_target_mesh.material_override = _target_mat
	add_child(_target_mesh)

	_label = Label3D.new()
	_label.position = Vector3(0, -0.8, 0)
	_label.pixel_size = 0.006
	_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	add_child(_label)

	_target = ik_target
	_show_fk()
	if not Engine.is_editor_hint():
		_print_check()


func _make_bone(length: float, color: Color) -> MeshInstance3D:
	var mesh_instance := MeshInstance3D.new()
	var capsule := CapsuleMesh.new()
	capsule.radius = 0.12
	capsule.height = length
	mesh_instance.mesh = capsule
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mesh_instance.material_override = mat
	return mesh_instance


func _unhandled_input(event: InputEvent) -> void:
	if Engine.is_editor_hint():
		return  # the toggles are for the running game, not the editor
	if not (event is InputEventKey and event.pressed and not event.echo):
		return
	if event.keycode == KEY_SPACE:
		_use_ik = not _use_ik
	elif event.keycode == KEY_U:
		_target = unreachable_target if _target == ik_target else ik_target
		_use_ik = true
	else:
		return
	if _use_ik:
		_show_ik()
	else:
		_show_fk()


## Joint positions [elbow_x, elbow_y, hand_x, hand_y] for local angles, as in fk.py.
## Plain floats (64-bit in GDScript); Vector2/Vector3 would round to 32-bit.
func forward(local_1_deg: float, local_2_deg: float) -> PackedFloat64Array:
	var g1 := deg_to_rad(local_1_deg)
	var g2 := deg_to_rad(local_1_deg + local_2_deg)
	var ex := shoulder_length * cos(g1)
	var ey := shoulder_length * sin(g1)
	return PackedFloat64Array([ex, ey, ex + elbow_length * cos(g2), ey + elbow_length * sin(g2)])


## True when |l1 - l2| <= d <= l1 + l2 (the check ik.py raises UnreachableTarget on).
func is_reachable(tx: float, ty: float) -> bool:
	var d := sqrt(tx * tx + ty * ty)
	return absf(shoulder_length - elbow_length) <= d and d <= shoulder_length + elbow_length


## Analytic 2-bone IK, same formula as ik.py. Only call it for reachable targets:
## the clamp below is for float rounding, not for reach.
func solve_two_bone_ik(l1: float, l2: float, tx: float, ty: float) -> PackedFloat64Array:
	var d := sqrt(tx * tx + ty * ty)
	var cos_alpha := clampf((l1 * l1 + l2 * l2 - d * d) / (2.0 * l1 * l2), -1.0, 1.0)
	var theta2 := 180.0 - rad_to_deg(acos(cos_alpha))
	var t2 := deg_to_rad(theta2)
	var reach_dir := rad_to_deg(atan2(l2 * sin(t2), l1 + l2 * cos(t2)))
	return PackedFloat64Array([rad_to_deg(atan2(ty, tx)) - reach_dir, theta2])


func _show_fk() -> void:
	_target_mesh.visible = false
	var j := forward(shoulder_angle_deg, elbow_angle_deg)
	_pose(j)
	_label.modulate = Color.WHITE
	_label.text = "FK  lokal %.1f / %.1f deg\nsiku (%.3f, %.3f)  tangan (%.3f, %.3f)" % [
		shoulder_angle_deg, elbow_angle_deg, j[0], j[1], j[2], j[3]]


func _show_ik() -> void:
	var tx := float(_target.x)
	var ty := float(_target.y)
	_target_mesh.visible = true
	_target_mesh.position = _target
	if is_reachable(tx, ty):
		var a := solve_two_bone_ik(shoulder_length, elbow_length, tx, ty)
		var j := forward(a[0], a[1])
		_pose(j)
		_target_mat.albedo_color = REACH_COLOR
		_label.modulate = Color.WHITE
		_label.text = "IK  theta1 %.2f  theta2 %.2f deg\nsiku (%.3f, %.3f)  tangan (%.3f, %.3f)" % [
			a[0], a[1], j[0], j[1], j[2], j[3]]
	else:
		# Not clamped silently: the arm points straight at the target and says why it stops short.
		_pose(forward(rad_to_deg(atan2(ty, tx)), 0.0))
		_target_mat.albedo_color = NO_REACH_COLOR
		_label.modulate = NO_REACH_COLOR
		_label.text = "IK  TARGET DI LUAR JANGKAUAN\nd = %.3f, batas [%.3f, %.3f]" % [
			sqrt(tx * tx + ty * ty), absf(shoulder_length - elbow_length), shoulder_length + elbow_length]


func _pose(j: PackedFloat64Array) -> void:
	var elbow := Vector3(j[0], j[1], 0)
	var hand := Vector3(j[2], j[3], 0)
	# Capsules are authored along +Y; point each from its start joint to its end joint.
	_place_bone(_shoulder_mesh, Vector3.ZERO, elbow)
	_place_bone(_elbow_mesh, elbow, hand)


func _place_bone(mesh_instance: MeshInstance3D, from: Vector3, to: Vector3) -> void:
	var dir := (to - from).normalized()
	mesh_instance.position = (from + to) * 0.5
	if dir.length() > 0.0001:
		mesh_instance.basis = Basis(Quaternion(Vector3.UP, dir))


## One line per check, parsed by Source/godot_check.py and compared with fk.py / ik.py.
func _print_check() -> void:
	var fk := forward(shoulder_angle_deg, elbow_angle_deg)
	print("ARM_FK local=%.12f,%.12f elbow=%.12f,%.12f hand=%.12f,%.12f" % [
		shoulder_angle_deg, elbow_angle_deg, fk[0], fk[1], fk[2], fk[3]])
	var tx := float(ik_target.x)
	var ty := float(ik_target.y)
	var a := solve_two_bone_ik(shoulder_length, elbow_length, tx, ty)
	var ik := forward(a[0], a[1])
	print("ARM_IK target=%.12f,%.12f theta=%.12f,%.12f hand=%.12f,%.12f" % [tx, ty, a[0], a[1], ik[2], ik[3]])
	for u in [unreachable_target, Vector3(0.5, 0, 0), ik_target]:
		print("ARM_REACH target=%.12f,%.12f reachable=%s" % [u.x, u.y, is_reachable(u.x, u.y)])
