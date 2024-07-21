import os.path
from os import path
from PIL import Image
from enum import Enum

class PropertyType(Enum):
	BOOL = 0
	INT = 1
	FLOAT = 2
	STRING = 3

class Properties:
	no_elements = 0
	data = [] #[[type,val], [type,val], ..]

	def append(self, name, type, value):
		self.data.append([name, type, value])
		self.no_elements += 1

	def print(self):
		print("-"*30)
		print("no_properties:", self.no_elements)
		for i in range(len(self.data)):
			print(self.data[i])
		print("-"*30)

class StaticTile:
	tile_index = -1			#int32
	blend_mode = 0			#byte
	
	tile_sheet_id = ""		#string - TODO better
	
	properties = None

class AnimatedTile:
	#type T -> based on style sheet
	#type S -> based in set if static tiles
	type = "S"				# S or T
	frame_interval = 0		#int32
	frame_count = 0			#int32
	no_properties = 0
	properties = []
	
	#for T
	style_sheet_id = ""		#string
	#for S
	tiles = []				#list of static tiles

class TileSheet:
	id = ""					#string
	desc = ""				#string
	img_src = ""			#string
	sheet_size = [0,0]		#pair of int32
	tile_size = [0,0]		#pair of int32
	margin = [0,0]			#pair of int32
	spacing = [0,0]			#pair of int32
	no_tiles = -1

	properties = None

	tile_images = []			#array of actual images
	tile_images_loaded = False
	
	tile_sheets_path = "tilesheets/"
	
	def printInfo(self):
		print("  <", self.id, "><", self.desc, "><", self.img_src, ">")
		print("    ", self.sheet_size, self.tile_size, self.margin, self.spacing)

	def setTileSheetSourceFolder(self, path):
		self.tile_sheets_path = path

	def loadImgSrc(self):
		self.no_tiles = self.sheet_size[0]*self.sheet_size[1]

		filename = self.tile_sheets_path + self.img_src
		
		#TODO besser
		#	filename may not specify type - if not set use .png
		if filename[-4] != ".":
			filename += ".png"
		
		print("trying to load tilesheet: ", filename)
		
		if not path.exists(filename) or not path.isfile(filename):
			print("could not find file")
			exit()
		
		self.tile_images = [ None for i in range( self.no_tiles ) ]
		
		img = Image.open(filename)
		width, height = img.size
		
		expected_width = self.sheet_size[0] * self.tile_size[0]
		expected_height = self.sheet_size[1] * self.tile_size[1]
		
		if width != expected_width or height != expected_height:
			print("invalid size", width, height, "vs", expected_width, expected_height)
			exit()
		
		index = 0
		for x in range( height//self.tile_size[0] ):
			for y in range( width//self.tile_size[1] ):
				area = ( y*self.tile_size[1], x*self.tile_size[0], (y+1)*self.tile_size[1], (x+1)*self.tile_size[0] )

				self.tile_images[index] = img.crop(area)
				index += 1
				#name = outFolder + str(y).zfill(2) + "_" + str(x).zfill(2) + ".png"
				#cropped_img.save(name)
		
		self.tile_images_loaded = True

class Layer:
	id = ""					#string
	visible = False			#bool
	desc = ""				#string	
	layer_size = [0,0]		#pair of int32
	tile_size = [0,0]		#pair of int32
	
	properties = None
	
	tiles = None
	
	def initTilesToNone(self):
		if self.tiles != None:
			return
		self.tiles = [[ None for x in range(self.layer_size[0]) ] for y in range(self.layer_size[1])]
	
	def printLayer(self):
		#print rough shape of layer to console
		print("Layer ", self.id, ":")
		border_str = "+" + "="*self.layer_size[0] + "+"
		print(border_str)
		
		for y in range(self.layer_size[1]):
			out = "H"
			for x in range(self.layer_size[0]):
				if self.tiles[y][x] == None:
					out += " "
				else:
					out += "#"
			out += "H"
			print(out)
		print(border_str)
	
	def printInfo(self):
		print("  <", self.id, "><", self.visible, "><", self.desc, "><", self.layer_size, "><", self.tile_size, ">")

class MapData:
	id = ""					#string
	desc = ""				#string
	
	properties = None
	
	no_tile_sheets = 0
	tile_sheets = []
	
	no_layers = 0
	layers = []
	
	output_folder = "out/"
	
	def createImage(self, save_layer_images = False):
		self.assertTileSheetImagesLoaded()

		#individual images per layer
		images = []
		for i in range(self.no_layers):
			print("creating layer ", i)
			img = self.createImageFromLayer(i, save_layer_images)
			images.append(img)
			
		#paste all layers onto first
		full_image = images[0].copy()
		print("creating final image")
		for i in range(1, len(images)):
			full_image.paste(images[i], (0,0), images[i])
	
		self.assertOutputFolderExists()
		full_image.save(self.output_folder + "allLayers.png")
		print("finished")
	
	def assertTileSheetImagesLoaded(self):
		for sheet in self.tile_sheets:
			sheet.loadImgSrc()
	
	def createImageFromLayer(self, layer_number, save_to_file = False):
		#TODO besser - tile_sets bereitmachen
		tile_set_dict = dict()
		for i, tile_set in enumerate(self.tile_sheets):
			tile_set_dict[tile_set.id] = tile_set
		
		layer = self.layers[layer_number]
		
		out_img_width = layer.layer_size[0] * layer.tile_size[0]
		out_img_height = layer.layer_size[1] * layer.tile_size[1]
		
		#print(out_img_width, out_img_height)
		
		#create full-size transparent image
		out_img = Image.new("RGBA",(out_img_width, out_img_height), (0,0,0,0))
		
		#paste non-null tile images
		for y in range( layer.layer_size[1] ):
			for x in range( layer.layer_size[0] ):
				tile = layer.tiles[y][x]
				if tile == None:
					continue
				x_pos = x * layer.tile_size[0]
				y_pos = y * layer.tile_size[1]
				img = tile_set_dict[tile.tile_sheet_id].tile_images[tile.tile_index]
				assert(tile_set_dict[tile.tile_sheet_id].id == tile.tile_sheet_id)
				#print(x_pos, y_pos, tile.tile_sheet_id, tile.tile_index, img)
				out_img.paste(img, (x_pos, y_pos))

		if save_to_file:
			self.assertOutputFolderExists()
			out_img.save(self.output_folder + "layer_" + str(layer_number) + "_" + layer.id + ".png")
		return out_img

	def setOutputFolder(self, path):
		self.output_folder = path

	def assertOutputFolderExists(self):
		if not os.path.exists(self.output_folder):
			os.makedirs(self.output_folder)

	def printInfo(self):
		print("-"*30)
		print("Map:")
		print("  id  : \"" + self.id + "\"")
		print("  desc: \"" + self.desc + "\"")

		print("  tile sheets:", self.no_tile_sheets)
		#for sheet in self.tile_sheets:
		#	sheet.printInfo()
		print("  layers:", self.no_layers)
		#for layer in self.layers:
		#	layer.printInfo()
		print("-"*30)

class MapLoader:
	def loadFromFile(self, filename):
		self.byteRunner = 0
		self.assertFileExists(filename)
		self.loadFile(filename)
		
		res = MapData()
		
		#first 6 bytes are "tBIN10"
		self.byteRunner += 6
		
		#map_id - string
		res.id = self.loadString()

		#map_description - string
		res.desc = self.loadString()
		
		#properties
		res.properties = self.loadProperties(False)
		
		#tile sheets
		res.no_tile_sheets, res.tile_sheets = self.loadTileSheets()
		
		#layers
		res.no_layers, res.layers = self.loadLayers()
		
		return res

	def loadFile(self, filename):
		inFile = open(filename, "rb")
		self.byteArray = inFile.read()
		inFile.close()
		self.byteRunner = 0

	def loadInt32(self):
		self.byteRunner += 4
		return int.from_bytes(self.byteArray[self.byteRunner-4:self.byteRunner], byteorder='little')

	def loadByte(self):
		self.byteRunner += 1
		return self.byteArray[self.byteRunner-1]

	def loadBool(self):
		return self.loadByte() > 0

	def loadSize(self):
		size = []
		size.append(self.loadInt32())	#width
		size.append(self.loadInt32())	#height
		return size

	def loadString(self):
		size = self.loadInt32()
		self.byteRunner += size
		return (self.byteArray[self.byteRunner-size:self.byteRunner]).decode("utf-8") 

	def loadProperties(self, print_ = True):
		noProperties = self.loadInt32()
		res = Properties()
		
		if(print_):
			print("noProperties:", noProperties)
		
		for i in range(noProperties):
			propName = self.loadString()
			#TODO PropertyType reihenfolge muss passen
			propType = PropertyType(self.loadByte())
			
			if(print_):
				print("  prop: <", propName, "> type:", propType.name)
		
			if( PropertyType.BOOL == propType ):	#0=bool
				value = self.loadBool()
			elif( PropertyType.INT == propType ):	#1=int
				value = self.loadInt32()
				if(print_):
					print("    value: <", value, ">")
			elif( PropertyType.FLOAT == propType ):	#float
				self.byteRunner += 4
				#exit(0)
			elif( PropertyType.STRING == propType ):	#string
				value = self.loadString()
				if(print_):
					print("    value: <", value, ">")
			else:
				print("error")
				exit(0)
			
			res.append(propName, propType, value)
		return res

	def loadStaticTile(self, tile_set_name):
		tile = StaticTile()

		tile.tile_index = self.loadInt32()
		'''
		if( not tileIndex in differentTypes ):
			differentTypes.append(tileIndex)
		'''
		tile.tile_sheet_id = tile_set_name
		tile.blend_mode = self.loadByte() 
		tile.properties = self.loadProperties(False)
		return tile

	def loadLayer(self, writeOut = False):
		layer = Layer()

		layer.id = self.loadString()
		layer.visible = self.loadBool()
		layer.desc = self.loadString()
		layer.layer_size = self.loadSize()
		layer.tile_size = self.loadSize()
		
		layer.properties = self.loadProperties(False)

		cur_tile_set = ""

		#initialize tiles to None
		layer.initTilesToNone()

		for y in range(layer.layer_size[1]):		#height
			x = 0
			
			while x < layer.layer_size[0]:			#width
				type = chr(self.loadByte())
				#print(x,y,type)
				
				if(type == 'T'):
					#Set currently used tile-sheet
					cur_tile_set = self.loadString()
				elif(type == 'N'):
					#Skip number of empty tiles
					nullCount = self.loadInt32();
					x += nullCount
				elif(type == 'S'):
					#Load Static tile
					layer.tiles[y][x] =  self.loadStaticTile(cur_tile_set)
					x+=1
				elif(type == 'A'):
					#Load animated tile
					#TODO for now first frame only
					
					frameInterval = self.loadInt32()
					tileFrameCount = self.loadInt32()
					todo_firstFrame = True
					while(tileFrameCount > 0):
						type = chr(self.loadByte())
						
						if(type == 'T'):
							cur_tile_set = self.loadString()
						elif(type == 'S'):
							#TODO for now only load first frame
							if todo_firstFrame:
								layer.tiles[y][x] =  self.loadStaticTile(cur_tile_set)
								todo_firstFrame = False
							else:
								self.loadStaticTile(cur_tile_set)
							
							tileFrameCount -= 1
						else:
							print("error")
							exit()
					self.loadProperties(False)
					
					x+=1
				else:
					print("error")
					exit()
		return layer

	def loadLayers(self):
		no_layers = self.loadInt32()
		layers = []
		
		for i in range(no_layers):
			layers.append( self.loadLayer() )
			#print(self.byteRunner, "/", len(self.byteArray))

		#print(self.byteRunner, "/", len(self.byteArray))
		#	expect eof
		assert(self.byteRunner == len(self.byteArray))

		return no_layers, layers

	def loadTileSheet(self):
		res = TileSheet()

		res.id = self.loadString()
		res.desc = self.loadString()
		res.img_src = self.loadString()
		res.sheet_size = self.loadSize()
		res.tile_size = self.loadSize()
		res.margin = self.loadSize()
		res.spacing = self.loadSize()
		res.properties = self.loadProperties(False)

		return res

	def loadTileSheets(self):
		no_tile_sheets = self.loadInt32()
		tile_sheets = []
		
		for i in range(no_tile_sheets):
			tile_sheets.append( self.loadTileSheet() )
		
		return no_tile_sheets, tile_sheets

	def assertFileExists(self, filename):
		#assert( path.exists(filename) )
		#assert( path.isfile(filename) )

		err = ""
		if not path.exists(filename):
			err = "file not found"
		elif not path.isfile(filename):
			err = "is not a file"
		
		if err != "":
			print("Error opening", "\"" + filename + "\":", err)
			exit(1)


def find_file():
    def print_error(folder):
        print(f"Error: no input file found")
        print(f"  put \".tbin\" file in folder \"{folder}\"")
    
    folder_path = "in"

    if not path.isdir(folder_path):
        print_error(folder_path)
        exit(1)

    filename = ""
    for fname in os.listdir(folder_path):
        if fname.lower().endswith(".tbin"):
            filename = fname
    
    if filename == "":
        print_error(folder_path)
        exit(1)
    
    file_path = os.path.join(folder_path, filename)
    print(f"working on file: \"{file_path}\"")
        
    return file_path
    

if __name__ == "__main__":
    filename = find_file()
    loader = MapLoader()

    mapData = loader.loadFromFile(filename)

    mapData.printInfo()

    save_layer_images = True
    mapData.createImage(save_layer_images)






