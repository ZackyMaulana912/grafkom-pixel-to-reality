@tool
extends Node3D
## My building: the room with the horse statue from Module 3
## (Module3/Source/data/mymodel.obj, copied unchanged to assets/ruangan/).
## Metres, y up, origin at the centre of the floor, same as Source/data/my_path.json.
## The texture is Module 3's atlas of my own photos, saved as PNG because Godot
## cannot import PPM.

@export var mesh: Mesh = preload("res://assets/ruangan/mymodel.obj")
@export var texture: Texture2D = preload("res://assets/ruangan/mymodel_tex.png")


func _ready() -> void:
	var instance := MeshInstance3D.new()
	instance.mesh = mesh
	var mat := StandardMaterial3D.new()
	mat.albedo_texture = texture
	mat.roughness = 0.9
	instance.material_override = mat
	add_child(instance)
