@tool
extends Node3D
## Module 4 -- interactive version of code/Module4/foot_slide_bug.py.
## Moves a stick-figure "character" forward at `scripted_speed` while a
## separate, purely visual leg-swing animates at `cycle_rate` cycles/second
## with a stride of `stride_per_cycle` metres. When scripted_speed !=
## stride_per_cycle * cycle_rate the figure visibly slides past its own
## footfall markers, which are dropped on the ground every half-cycle so the
## gap is measurable, not just a vibe.
##
## 2026-09-29: @tool (the figure is visible, standing, in the editor); the
## capsule became a stick figure whose legs actually swing (the comment above
## always promised a leg-swing); markers are children of this node, so they
## land under the figure wherever the Walker node is placed; the walk restarts
## every `loop_seconds` so the figure stays in view.
##
## Module 4 (mine, T11): measured with tools/cek_walker.gd, the planted foot slid
## 31.5 cm per step even at the "fixed" speed stride_per_cycle x cycle_rate, because
## stride_per_cycle (1.0) is a typed number while these legs cover 1.60 m per cycle,
## and it rose 9.2 cm because the hips barely bob. With `use_root_motion` (default)
## the body is moved by exactly what the planted foot moved back relative to the
## body this frame, and lifted so that foot stays on the floor; footfall markers sit
## where the foot really landed and turn red if that foot then slid more than 5 cm.
## [F] switches to the starter behaviour (constant scripted_speed) and back.

@export var scripted_speed: float = 1.5
@export var stride_per_cycle: float = 1.0
@export var cycle_rate: float = 1.0
@export var loop_seconds: float = 8.0
@export var use_root_motion: bool = true
@export var show_markers: bool = true   # tools/cek_walker.gd turns them off while measuring

const SLIDE_LIMIT := 0.05

const LIMB_COLOR := Color(0.91, 0.96, 0.93)
const JOINT_COLOR := Color(0.83, 0.65, 0.22)
const LIMB_RADIUS := 0.035

var _body: Node3D          # the figure's root; moves along +x
var _hips: Node3D
var _thighs: Array[Node3D] = []
var _knees: Array[Node3D] = []
var _feet: Array[Node3D] = []
var _shoulders: Array[Node3D] = []
var _elbows: Array[Node3D] = []
var _markers: Node3D
var _label: Label3D
var _t := 0.0
var _next_footfall_t := 0.0
var _step := 0
var _was_planted := [false, false]
var _landing := [Vector3.ZERO, Vector3.ZERO]
var _last_planted := [Vector3.ZERO, Vector3.ZERO]
var _last_slide := 0.0
var _foot_ground_y := 0.0   # height of a planted foot's centre in the standing pose


func _ready() -> void:
	_body = Node3D.new()
	add_child(_body)
	_build_stick_figure(_body)
	_markers = Node3D.new()
	add_child(_markers)
	_label = Label3D.new()
	_label.position = Vector3(0, 2.3, 0)
	_label.pixel_size = 0.006
	_body.add_child(_label)
	_pose(0.0)
	_foot_ground_y = _foot_local(_stance_leg()).y
	_update_label()


func _process(delta: float) -> void:
	if Engine.is_editor_hint():
		return  # stand still in the editor; walk only while playing
	_t += delta
	if _t > loop_seconds:
		_restart()
	if use_root_motion:
		_root_motion_step(TAU * cycle_rate * _t)
	else:
		_body.position.x = scripted_speed * _t
		_pose(TAU * cycle_rate * _t)  # one gait cycle every 1 / cycle_rate seconds
		# starter markers: dropped every half-cycle where the typed stride says the foot is
		var half_cycle := 1.0 / (2.0 * cycle_rate)
		if _t >= _next_footfall_t and show_markers:
			_drop_footfall(_t)
			_next_footfall_t += half_cycle
	_track_feet()


## Advance the pose to `phase`, then move the body so the planted foot keeps its place.
func _root_motion_step(phase: float) -> void:
	var leg := _stance_leg_at(phase)
	var before := _foot_local(leg)
	_pose(phase)
	var after := _foot_local(leg)
	_body.position.x += before.x - after.x
	_body.position.y = _foot_ground_y - after.y


## The leg whose knee is straight carries the body (_pose bends only the swinging knee).
func _stance_leg_at(phase: float) -> int:
	return 0 if cos(phase) <= 0.0 else 1


func _stance_leg() -> int:
	return 0 if _knees[0].rotation.z == 0.0 else 1


## A foot's centre in the body's own frame: its local transforms composed up to _body,
## the same root-to-leaf chain as fk.py (no world positions involved).
func _foot_local(leg: int) -> Vector3:
	var p := _feet[leg].position
	var n := _feet[leg].get_parent() as Node3D
	while n != _body:
		p = n.transform * p
		n = n.get_parent() as Node3D
	return p


## Root-motion markers: one where each foot lands, red if it then slides more than SLIDE_LIMIT.
func _track_feet() -> void:
	for i in 2:
		var planted: bool = _knees[i].rotation.z == 0.0
		var p := _feet[i].global_position
		if planted and not _was_planted[i]:
			_landing[i] = p
		if planted:
			_last_planted[i] = p
		elif _was_planted[i]:
			# measured up to the last planted frame, as tools/cek_walker.gd does
			_last_slide = _last_planted[i].x - _landing[i].x
			if use_root_motion and show_markers:
				_drop_marker(to_local(_landing[i]), absf(_last_slide) > SLIDE_LIMIT)
			_update_label()
		_was_planted[i] = planted


func _update_label() -> void:
	_label.text = ("root motion dari kaki" if use_root_motion else "scripted_speed %.2f m/s" % scripted_speed) \
		+ "\ngeser kaki langkah terakhir %.1f cm  [F]" % (100.0 * _last_slide)


func _unhandled_input(event: InputEvent) -> void:
	if Engine.is_editor_hint():
		return
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_F:
		use_root_motion = not use_root_motion
		_restart()


func _restart() -> void:
	_t = 0.0
	_next_footfall_t = 0.0
	_step = 0
	_last_slide = 0.0
	_body.position = Vector3.ZERO
	_pose(0.0)
	_was_planted = [false, false]
	_last_planted = [Vector3.ZERO, Vector3.ZERO]
	for m in _markers.get_children():
		m.queue_free()
	_update_label()


func _drop_marker(local_pos: Vector3, slid: bool) -> void:
	var marker := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = Vector3(0.3, 0.02, 0.15)
	marker.mesh = box
	marker.position = Vector3(local_pos.x, 0.01, local_pos.z)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.9, 0.2, 0.2) if slid else Color(0.2, 0.9, 0.3)
	marker.material_override = mat
	_markers.add_child.call_deferred(marker)


func _drop_footfall(t: float) -> void:
	var marker := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = Vector3(0.3, 0.02, 0.15)
	marker.mesh = box
	# Where the animation's own stride says the foot should be planted,
	# alternating left and right foot.
	var animated_x: float = stride_per_cycle * cycle_rate * t
	var side := 1.0 if _step % 2 == 0 else -1.0
	_step += 1
	marker.position = Vector3(animated_x, 0.01, 0.12 * side)
	var mat := StandardMaterial3D.new()
	var slide: float = scripted_speed * t - animated_x
	mat.albedo_color = Color(0.9, 0.2, 0.2) if abs(slide) > 0.05 else Color(0.2, 0.9, 0.3)
	marker.material_override = mat
	_markers.add_child.call_deferred(marker)


# ---------------------------------------------------------------- the figure
# About 1.8 m tall, facing +x: hips -> spine -> neck/head, neck -> shoulders ->
# upper arm -> forearm, hips -> thigh -> shin -> foot. Each joint is a Node3D
# whose rotation is local to its parent -- the same tree of local transforms
# as fk.py, in 3D.

func _build_stick_figure(root: Node3D) -> void:
	_hips = _joint(root, Vector3(0, 0.95, 0))
	_bone(_hips, 0.55, true)                                   # spine
	var neck := _joint(_hips, Vector3(0, 0.55, 0))
	_bone(neck, 0.07, true)
	var head := MeshInstance3D.new()
	var head_mesh := SphereMesh.new()
	head_mesh.radius = 0.12
	head_mesh.height = 0.24
	head.mesh = head_mesh
	head.position = Vector3(0, 0.19, 0)
	head.material_override = _material(LIMB_COLOR)
	neck.add_child(head)
	_crossbar(neck, 0.4)                                       # shoulders
	_crossbar(_hips, 0.24)                                     # pelvis
	for side in [1.0, -1.0]:
		var shoulder := _joint(neck, Vector3(0, 0, 0.2 * side))
		_bone(shoulder, 0.3)
		var elbow := _joint(shoulder, Vector3(0, -0.3, 0))
		_bone(elbow, 0.28)
		_shoulders.append(shoulder)
		_elbows.append(elbow)
		var thigh := _joint(_hips, Vector3(0, 0, 0.12 * side))
		_bone(thigh, 0.45)
		var knee := _joint(thigh, Vector3(0, -0.45, 0))
		_bone(knee, 0.45)
		var foot := MeshInstance3D.new()
		var foot_mesh := BoxMesh.new()
		foot_mesh.size = Vector3(0.2, 0.04, 0.08)
		foot.mesh = foot_mesh
		foot.position = Vector3(0.06, -0.47, 0)
		foot.material_override = _material(LIMB_COLOR)
		knee.add_child(foot)
		_feet.append(foot)
		_thighs.append(thigh)
		_knees.append(knee)


## One gait cycle over phase 0..TAU: legs swing, the swinging knee bends, the
## arms swing opposite the legs, the hips bob a little. Rotating about z by
## +angle moves a downward limb toward +x (forward).
func _pose(phase: float) -> void:
	var s := sin(phase)
	for i in range(2):
		var sgn := 1.0 if i == 0 else -1.0
		var leg_phase := phase + (0.0 if i == 0 else PI)
		_thighs[i].rotation.z = 0.45 * sgn * s
		_knees[i].rotation.z = -0.63 * max(0.0, cos(leg_phase))
		_shoulders[i].rotation.z = -0.35 * sgn * s
		_elbows[i].rotation.z = 0.35
	_hips.position.y = 0.95 + 0.03 * abs(cos(phase))


func _joint(parent: Node3D, pos: Vector3) -> Node3D:
	var j := Node3D.new()
	j.position = pos
	parent.add_child(j)
	var ball := MeshInstance3D.new()
	var ball_mesh := SphereMesh.new()
	ball_mesh.radius = LIMB_RADIUS * 1.5
	ball_mesh.height = LIMB_RADIUS * 3.0
	ball.mesh = ball_mesh
	ball.material_override = _material(JOINT_COLOR)
	j.add_child(ball)
	return j


## A limb segment hanging down from `parent` (or pointing up when `up`).
func _bone(parent: Node3D, length: float, up: bool = false) -> void:
	var m := MeshInstance3D.new()
	var c := CylinderMesh.new()
	c.top_radius = LIMB_RADIUS
	c.bottom_radius = LIMB_RADIUS
	c.height = length
	m.mesh = c
	m.position = Vector3(0, length * 0.5 if up else -length * 0.5, 0)
	m.material_override = _material(LIMB_COLOR)
	parent.add_child(m)


## A horizontal bar across the body (shoulders, pelvis), along z.
func _crossbar(parent: Node3D, width: float) -> void:
	var m := MeshInstance3D.new()
	var c := CylinderMesh.new()
	c.top_radius = LIMB_RADIUS
	c.bottom_radius = LIMB_RADIUS
	c.height = width
	m.mesh = c
	m.rotation.x = PI / 2
	m.material_override = _material(LIMB_COLOR)
	parent.add_child(m)


func _material(color: Color) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	return mat
