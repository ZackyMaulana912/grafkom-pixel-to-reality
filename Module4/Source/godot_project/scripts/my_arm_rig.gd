@tool
extends Node3D
## My own arm as a Godot Skeleton3D: shoulder -> elbow -> wrist -> middle fingertip,
## lengths and local angles read from res://data/my_chain.json (copy of
## Source/data/my_chain.json, measured from my arm and photo IMG_9035).
## Each bone's rest is "walk along the parent's x by the parent's length", and its
## pose is a rotation about z by the local angle, so Skeleton3D's own global pose
## IS forward kinematics; the printed joints are compared with fk.py by godot_check.py.

@export var chain_json: String = "res://data/my_chain.json"
@export var bone_radius: float = 0.022

var skeleton: Skeleton3D


func _ready() -> void:
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(chain_json))
	var scale_to_m: float = 0.01 if data["unit"] == "cm" else 1.0
	skeleton = Skeleton3D.new()
	add_child(skeleton)
	var colors := [Color(0.2, 0.6, 1.0), Color(1.0, 0.6, 0.1), Color(0.3, 0.8, 0.4)]
	var parent := -1
	var parent_length := 0.0
	var lengths: Array[float] = []
	for i in data["bones"].size():
		var bone: Dictionary = data["bones"][i]
		var idx := skeleton.add_bone("bone_%d" % i)
		skeleton.set_bone_parent(idx, parent)
		skeleton.set_bone_rest(idx, Transform3D(Basis(), Vector3(parent_length, 0, 0)))
		skeleton.set_bone_pose_position(idx, Vector3(parent_length, 0, 0))
		skeleton.set_bone_pose_rotation(idx, Quaternion(Vector3.BACK, deg_to_rad(bone["local_angle_deg"])))
		parent = idx
		parent_length = float(bone["length"]) * scale_to_m
		lengths.append(parent_length)
	var tip := skeleton.add_bone("ujung_jari")
	skeleton.set_bone_parent(tip, parent)
	skeleton.set_bone_rest(tip, Transform3D(Basis(), Vector3(parent_length, 0, 0)))
	skeleton.set_bone_pose_position(tip, Vector3(parent_length, 0, 0))
	for i in lengths.size():
		_attach_capsule(i, lengths[i], colors[i % colors.size()])
	if not Engine.is_editor_hint():
		_print_check.call_deferred()


func _attach_capsule(bone: int, length: float, color: Color) -> void:
	var attach := BoneAttachment3D.new()
	skeleton.add_child(attach)
	attach.bone_idx = bone
	var m := MeshInstance3D.new()
	var capsule := CapsuleMesh.new()
	capsule.radius = bone_radius
	capsule.height = length
	m.mesh = capsule
	# capsules are authored along +y; lay it along the bone's +x, centred on the bone
	m.transform = Transform3D(Basis(Vector3.BACK, -PI / 2), Vector3(length * 0.5, 0, 0))
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	m.material_override = mat
	attach.add_child(m)


## Joint positions in the rig's own plane (skeleton space, metres), parsed by godot_check.py.
func _print_check() -> void:
	var parts := []
	for b in skeleton.get_bone_count():
		var p := skeleton.get_bone_global_pose(b).origin
		parts.append("%.9f,%.9f,%.9f" % [p.x, p.y, p.z])
	print("MYARM joints=%s" % ";".join(parts))
