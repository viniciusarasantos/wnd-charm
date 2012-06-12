#!/usr/bin/env python

from . import pychrm

# FeatureRegistration.py is where the SWIG wrapped objects get put into a dict
# for use in signature calculation
from . import FeatureRegistration 

# FeatureNameMap.py contains mapping from old style names to new style
# and the function TranslateFeatureNames()
from . import FeatureNameMap

import numpy as np
from StringIO import StringIO
try:
	import cPickle as pickle
except:
	import pickle

# os module has function os.walk( ... )
import os
import os.path 
import re


# Initialize module level globals
Algorithms = None
Transforms = None
small_featureset_featuregroup_strings = None
large_featureset_featuregroup_strings = None
small_featureset_featuregroup_list = None
large_featureset_featuregroup_list = None

error_banner = "\n*************************************************************************\n"

def initialize_module(): 
	# If you're going to calculate any signatures, you need this stuff
	# FIXME: Maybe rig something up using a load on demand?
	global Algorithms
	global Transforms
	global small_featureset_featuregroup_strings
	global large_featureset_featuregroup_strings
	global small_featureset_featuregroup_list
	global large_featureset_featuregroup_list

	Algorithms = FeatureRegistration.LoadFeatureAlgorithms()
	Transforms = FeatureRegistration.LoadFeatureTransforms()

	feature_lists = FeatureRegistration.LoadSmallAndLargeFeatureSetStringLists()

	small_featureset_featuregroup_strings = feature_lists[0]
	full_list = "\n"
	large_featureset_featuregroup_strings = full_list.join( feature_lists )

	small_featureset_featuregroup_list = []
	for fg_str in small_featureset_featuregroup_strings.splitlines():
		fg = ParseFeatureGroupString( fg_str )
		small_featureset_featuregroup_list.append( fg )

	large_featureset_featuregroup_list = []
	for fg_str in large_featureset_featuregroup_strings.splitlines():
		fg = ParseFeatureGroupString( fg_str )
		large_featureset_featuregroup_list.append( fg )

#############################################################################
# class definition of FeatureVector
#############################################################################
# FeatureVector inherits from class object and is thus a Python "new-style" class
class FeatureVector(object):
	"""
	FIXME: Would be nice to define a [] operator that returns
	       a tuple = (self.names[n], self.values[n])
	"""
	names = None
	values = None
	#================================================================
	def __init__( self ):
		"""@brief: constructor
		"""
		self.names = []
		self.values = []
	#================================================================
	def is_valid( self ):
		"""
		@brief: an instance should know all the criteria for being a valid FeatureVector
		"""
		if len( self.values ) != len( self.names ):
			raise RuntimeError( "Instance of {} is invalid: ".format( self.__class__ ) + \
			  "different number of values ({}) and names ({}).".format( \
			  len( self.feature_values ), len( self.feature_names ) ) )
		return True

#############################################################################
# class definition of FeatureWeights
#############################################################################
class FeatureWeights( FeatureVector ):
	"""
	"""
	def __init__( self ):
		# call parent constructor
		super( FeatureWeights, self ).__init__()

	#================================================================
	@classmethod
	def NewFromFile( cls, weights_filepath ):
		"""@brief written to read in files created by wndchrm -vw/path/to/weightsfile.txt"""

		weights = cls()
		with open( weights_filepath, 'r' ) as weights_file:
			for line in weights_file:
				# split line "number <space> name"
				feature_line = line.strip().split( " ", 1 )
				weights.values.append( float( feature_line[0] ) )
				weights.names.append( feature_line[1] )
		return weights

	#================================================================
	def EliminateZeros( self ):
		"""@breif Good for Fisher scores, N/A for Pearson scores - FIXME: subclass!"""

		scores = zip( self.names, self.values )
		nonzero_scores = [ (name, weight) for name, weight in scores if weight != 0 ]
		self.names, self.values = zip( *nonzero_scores )

	#================================================================
	def Threshold( self, num_features_to_be_used  ):
		"""@breif Good for Fisher scores, N/A for Pearson scores - FIXME: subclass!"""

		raw_featureweights = zip( self.names, self.values )
		# raw_featureweights is now a list of tuples := [ (name1, value1), (name2, value2), ... ]

		# sort from max to min
		# sort by the second item in the tuple, i.e., index 1
		sort_func = lambda feat_a, feat_b: cmp( feat_a[1], feat_b[1] ) 

		sorted_featureweights = sorted( raw_featureweights, sort_func, reverse = True )
		# take top N features
		use_these_feature_weights = \
				list( itertools.islice( sorted_featureweights, num_features_to_be_used ) )
		
		self.names, self.values = zip( *use_these_feature_weights )


#############################################################################
# class definition of Signatures
#############################################################################
class Signatures( FeatureVector ):
	"""
	"""

	path_to_image_file = None
	options = ""

	#================================================================
	def __init__( self ):
		"""@brief: constructor
		"""
		# call parent constructor
		super( Signatures, self ).__init__()

	#================================================================
	@classmethod
	def SmallFeatureSet( cls, imagepath, options = None ):
		"""@brief Equivalent of invoking wndchrm train in c-chrm
		@argument path - path to a tiff file
		@return An instance of the class Signatures for image with sigs calculated."""

		print "====================================================================="
		print "Calculating small feature set for file:"
		global small_featureset_featuregroup_list
		return cls.FromFeatureGroupList( imagepath, small_featureset_featuregroup_list, options )

	#================================================================
	@classmethod
	def LargeFeatureSet( cls, imagepath, options = None ):
		"""@brief Equivalent of invoking wndchrm train -l in c-chrm
		@argument path - path to a tiff file
		@return An instance of the class Signatures for image with sigs calculated."""

		print "====================================================================="
		print "Calculating large feature set for file:"

		global large_featureset_featuregroup_list
		retval = None

		if options == None:
			retval = cls.FromFeatureGroupList( imagepath, large_featureset_featuregroup_list, "-l" )
		else:
			# FIXME: dummyproofing: does options already contain '-l'?
			retval = cls.FromFeatureGroupList( imagepath, large_featureset_featuregroup_list, \
					options + "-l" )
		return retval

	#================================================================
	@classmethod
	def FromFeatureGroupList( cls, path_to_image, feature_groups, options = None ):
		"""@brief calculates signatures

		@remarks: Currently, you are not allowed to ask for a Signatures using a feature list,
		but instead use this call with a feature group list, load the signature into a
		TrainingSet instance, then call TrainingSet.FeatureReduce.
		"""

		print path_to_image
		# derive the name of the sig/pysig file that would exist if there were one
		# given the options requested

		sigpath = None
		root, extension = os.path.splitext( path_to_image )
		options_str = options if options else ""

		# FIXME: Do a sanity check to see that the sig file contains sigs that match
		#        given the options and the features requested
		sigpath = root + options + ".pysig"
		if os.path.exists( sigpath ):
			return cls.FromSigFile( path_to_image, sigpath, options )
		
		sigpath = root + options + ".sig" 
		if os.path.exists( sigpath ):
			return cls.FromSigFile( path_to_image, sigpath, options )

		# All hope is lost. Calculate sigs
		original = pychrm.ImageMatrix()
		if 1 != original.OpenImage( path_to_image, 0, None, 0, 0 ):
			raise ValueError( 'Could not build an ImageMatrix from {}, check the path.'.\
			    format( path_to_image ) )

		im_cache = {}
		im_cache[ '' ] = original

		# instantiate an empty Signatures object
		signatures = cls()
		signatures.path_to_image_file = path_to_image
		signatures.options = options

		for fg in feature_groups:
			print "Group {}".format( fg.Name )
			returned_feature_vals = fg.CalculateFeatures( im_cache )
			count = 0
			for value in returned_feature_vals:
				signatures.names.append( fg.Name + " [{}]".format( count ) )
				signatures.values.append( value )	
				count += 1

		return signatures

	#================================================================
	@classmethod
	def FromPickle( cls, path ):
		"""
		FIXME: Implement!
		"""
		pass

	#================================================================
	def PickleMe( self ):
		"""
		FIXME: Implement!
		"""
		pass

	#================================================================
	@classmethod
	def FromSigFile( cls, image_path, sigfile_path, options = None ):
		"""@argument sigfile_path must be a .sig or a .pysig file
		
		@remarks - old style sig files don't know about their options other than 
		           the information contained in the name. In the future pysig files
							 may keep that info within the file. Thus, for now, the argument
							 options is something set externally rather than gleaned from
							 reading the file."""

		print "Loading features from sigfile {}".format( sigfile_path )

		signatures = cls()
		signatures.path_to_image_file = image_path
		signatures.options = options

		with open( sigfile_path ) as infile:
			linenum = 0
			for line in infile:
				if linenum == 0:
					# The class id here may be trash
					signatures.class_id = line.strip()
					pass
				elif linenum == 1:
					signatures.path_to_image_file = line.strip()
				else:
					value, name = line.strip().split( ' ', 1 )
					signatures.values.append( float( value ) )
					signatures.names.append( name )
				linenum += 1
		
		return signatures
	
	#================================================================
	def	WriteFeaturesToASCIISigFile( self, filepath = None ):
		"""Write a sig file.
		
		If filepath is specified, you get to name it whatever you want and put it
		wherever you want. Otherwise, it's named according to convention and placed 
		next to the image file in its directory."""

		self.is_valid()

		outfile_path = ""
		if not filepath or filepath == "":
			if not self.path_to_image_file or self.path_to_image_file == "":
				raise ValueError( "Can't write sig file. No filepath specified in function call, and no path associated with this instance of Signatures." )
			outfile_path = self.path_to_image_file

			path, filename = os.path.split( outfile_path )
			if not os.path.exists( path ):
				raise ValueError( 'Invalid path {}'.format( path ) )

			filename_parts = filename.rsplit( '.', 1 )
			if self.options and self.options is not "":
				outfile_path = "{}{}.pysig".format( filename_parts[0],\
																					self.options if self.options else "" )
			else:
				outfile_path = "{}.pysig".format( filename_parts[0] )
			outfile_path = os.path.join( path, outfile_path )

		if os.path.exists( outfile_path ):
			print "Overwriting {}".format( outfile_path )
		else:
			print 'Writing signature file "{}"'.format( outfile_path )

		with open( outfile_path, "w" ) as out_file:
			# FIXME: line 2 contains class membership, just hardcode a number for now
			out_file.write( "0\n" )
			out_file.write( "{}\n".format( self.path_to_image_file ) )
			for i in range( 0, len( self.feature_names ) ):
				out_file.write( "{val:0.6f} {name}\n".format( val=self.values[i], name=self.names[i] ) )


# end definition class Signatures

#############################################################################
# class definition of FeatureGroup
#############################################################################
class FeatureGroup:
	"""
	Attributes Name, Alg and Tforms are references to the SWIG objects
	"""

	Name = ""
	Alg = None
	Tforms = []
	def __init__( self, name_str = "", algorithm = None, tform_list = [] ):
		#print "Creating new FeatureGroup for string {}:".format(name_str)
		#print "\talgorithm: {}, transform list: {}".format( algorithm, tform_list )
		self.Name = name_str 
		self.Alg = algorithm
		self.Tforms = tform_list
	def CalculateFeatures( self, cached_pixel_planes ):
		"""Returns a tuple with the features"""
		pixel_plane = None
		try:
			#print "transforms: {}".format( self.Tforms )
			pixel_plane = RetrievePixelPlane( cached_pixel_planes, self.Tforms )
		except:
			raise
		return self.Alg.calculate( pixel_plane )


#############################################################################
# global functions
#############################################################################
def RetrievePixelPlane( image_matrix_cache, tform_list ):
	"""
	Returns the image matrix prescribed in tform_list
	If it already exists in cache, just return.
	If it doesn't exist calculates it
	Recurses through the compound transform chain in tform_list
	"""
	#print "passed in: {}".format( tform_list )
	requested_transform = " ".join( [ tform.name for tform in tform_list ] )
	#print "requesting pixel plane: '{}'".format( requested_transform )
	if requested_transform in image_matrix_cache:
		return image_matrix_cache[ requested_transform ]
	
	# Required transform isn't in the cache, gotta make it
	# Pop transforms off the end sequentially and check to see if
	# lower-level transforms have already been calculated and stored in cache

	# Can't begin if there isn't at least the raw (untransformed) pixel plane
	# already stored in the cache
	if image_matrix_cache is None or len(image_matrix_cache) == 0:
		raise ValueError( "Can't calculate features: couldn't find the original pixel plane" +\
		                  "to calculate features {}.".format( self.Name ) )

	sublist = tform_list[:]
	sublist.reverse()
	top_level_transform = sublist.pop()
	intermediate_pixel_plane = RetrievePixelPlane( image_matrix_cache, sublist )

	tformed_pp = top_level_transform.transform( intermediate_pixel_plane )
	#assert( intermediate_pixel_plane ), "Pixel Plane returned from transform() was NULL"
	image_matrix_cache[ requested_transform ] = tformed_pp
	return tformed_pp

#================================================================
def ParseFeatureGroupString( name ):
	"""Takes a string input, parses, and returns an instance of a FeatureGroup class"""
	#TBD: make a member function of the FeatureGroup
	# get the algorithm

	global Algorithms
	global Transforms
	string_rep = name.rstrip( ")" )
	parsed = string_rep.split( ' (' )
	
	alg = parsed[0]
	if alg not in Algorithms:
		raise KeyError( "Don't know about a feature algorithm with the name {}".format(alg) )
	
	tform_list = parsed[1:]
	try:
		tform_list.remove( "" )
	except ValueError:
		pass
	if len(tform_list) != 0:
		for tform in tform_list:
			if tform not in Transforms:
				raise KeyError( "Don't know about a transform named {}".format( tform ) )

	tform_swig_obj_list = [ Transforms[ tform ] for tform in tform_list ]

	return FeatureGroup( name, Algorithms[ alg ], tform_swig_obj_list )

#================================================================
def GenerateWorkOrderFromListOfFeatureStrings( feature_list ):
	"""
	Takes list of feature strings and chops off bin number at the first space on right, e.g.,
	"feature alg (transform()) [bin]" ... Returns a list of FeatureGroups.
	@return work_order - list of FeatureGroup objects
	@return output_features_count - total number of individual features contained in work_order
	"""

	feature_group_strings = set()
	output_features_count = 0

	for feature in feature_list:
		split_line = feature.rsplit( " ", 1 )
		# add to set to ensure uniqueness
		feature_group_strings.add( split_line[0] )

	# iterate over set and construct feature groups
	work_order = []
	for feature_group in feature_group_strings:
		fg = ParseFeatureGroupString( feature_group )
		output_features_count += fg.Alg.n_features
		work_order.append( fg )

	return work_order, output_features_count

#############################################################################
# class definition of TrainingSet
#############################################################################
class TrainingSet:
	"""
  """

	# source_path - could be the name of a .fit, or pickle file from which this
	# instance was generated, could be a directory
	# source_path is essentially a name
	# might want to make separate name member in the future
	source_path = ""
	num_classes = -1
	num_features = -1
	num_images = -1

	# For C classes, each with Ni images and M features:
	# If the dataset is contiguous, C = 1

	# A list of numpy matrices, length C (one Ni x M matrix for each class)
	# The design is such because it's useful to be able to quickly collect feature statistics
	# across an image class excluding the other classes
	data_list = None

	# A list of strings, length C
	classnames_list = None

	# A list of strings length M
	featurenames_list = None

	# a list of lists, length C, where each list is length Ni, contining pathnames of tiles/imgs
	imagenames_list = None

	# The following class members are optional:
	# normalized_against is a string that keeps track of whether or not self has been
	# normalized. For test sets, value will be the source_path of the training_set.
	# For training sets, value will be "itself"
	normalized_against = None

	# Stored feature maxima and minima go in here
	# only exist, if self has been normalized against itself
	feature_maxima = None
	feature_minima = None

	# A list of floats against which marg probs can be multiplied
	# to obtain an interpolated value
	interpolation_coefficients = None

	# keep track of all the options (-l -S###, etc)
	# FIXME: expand to have all options kept track of individually
	feature_options = None

	def __init__( self, data_dict = None):
		"""
		TrainingSet constructor
		"""

		self.data_list = []
		self.classnames_list = []
		self.featurenames_list = []
		self.imagenames_list = []

		if data_dict != None:
			if "source_path" in data_dict:
				self.source_path = data_dict[ 'source_path' ]
			if "num_classes" in data_dict:
				self.num_classes = data_dict[ 'num_classes' ]
			if "num_features" in data_dict:
				self.num_features = data_dict[ 'num_features' ]
			if "num_images" in data_dict:
				self.num_images = data_dict[ 'num_images' ]
			if "data_list" in data_dict:
				self.data_list = data_dict[ 'data_list' ]
			if "classnames_list" in data_dict:
				self.classnames_list = data_dict[ 'classnames_list' ]
			if "featurenames_list" in data_dict:
				self.featurenames_list = data_dict[ 'featurenames_list' ]
			if "imagenames_list" in data_dict:
				self.imagenames_list = data_dict[ 'imagenames_list' ]
			if "feature_maxima" in data_dict:
				self.feature_maxima = data_dict[ 'feature_maxima' ]
			if "feature_minima" in data_dict:
				self.feature_minima = data_dict[ 'feature_minima' ]
			if "interpolation_coefficients" in data_dict:
				self.interpolation_coefficients = data_dict[ 'interpolation_coefficients' ]

  #=================================================================================
	@classmethod
	def NewFromPickleFile( cls, pathname ):
		"""
		The pickle is in the form of a dict
		FIXME: Shouldn't call Normalize if feature_maxima/minima are in the data_dict
		"""
		path, filename = os.path.split( pathname )
		if filename == "":
			raise ValueError( 'Invalid pathname: {}'.format( pathname ) )

		if not filename.endswith( ".fit.pickled" ):
			raise ValueError( 'Not a pickled TrainingSet file: {}'.format( pathname ) )

		print "Loading Training Set from pickled file {}".format( pathname )
		unpkled = None
		the_training_set = None
		with open( pathname, "rb" ) as pkled_in:
			the_training_set = cls( pickle.load( pkled_in ) )

		# it might already be normalized!
		# FIXME: check for that
		# the_training_set.Normalize()

		return the_training_set

  #=================================================================================
	@classmethod
	def NewFromFitFile( cls, pathname ):
		"""
		Helper function which reads in a c-chrm fit file, builds a dict with the info
		Then calls the constructor and passes the dict as an argument
		"""
		path, filename = os.path.split( pathname )
		if filename == "":
			raise ValueError( 'Invalid pathname: {}'.format( pathname ) )

		if not filename.endswith( ".fit" ):
			raise ValueError( 'Not a .fit file: {}'.format( pathname ) )

		pickled_pathname = pathname + ".pychrm"

		print "Creating Training Set from legacy WND-CHARM text file file {}".format( pathname )
		with open( pathname ) as fitfile:
			data_dict = {}
			data_dict[ 'source_path' ] = pathname
			data_dict[ 'data_list' ] = []
			data_dict[ 'imagenames_list' ] = []
			data_dict[ 'featurenames_list' ] = []
			data_dict[ 'classnames_list' ] = []
			data_dict[ 'imagenames_list' ] = []
			data_dict[ 'data_list' ] = []
			tmp_string_data_list = []

			name_line = False
			line_num = 0
			feature_count = 0
			image_pathname = ""
			num_classes = 0
			num_features = 0

			for line in fitfile:
				if line_num is 0:
					num_classes = int( line )
					data_dict[ 'num_classes' ] = num_classes
					# initialize list for string data
					for i in range( num_classes ):
						tmp_string_data_list.append( [] )
						data_dict[ 'imagenames_list' ].append( [] )
				elif line_num is 1:
					num_features = int( line )
					data_dict[ 'num_features' ] = num_features
				elif line_num is 2:
					data_dict[ 'num_images' ] = int( line )
				elif line_num <= ( num_features + 2 ):
					data_dict[ 'featurenames_list' ].append( line.strip() )
					feature_count += 1
				elif line_num == ( num_features + 3 ):
					pass # skip a line
				elif line_num <= ( num_features + 3 + num_classes ):
					data_dict[ 'classnames_list' ].append( line.strip() )
				else:
					# Read in features
					# Comes in alternating lines of data, then tile name
					if not name_line:
						# strip off the class identity value, which is the last in the array
						split_line = line.strip().rsplit( " ", 1)
						#print "class {}".format( split_line[1] )
						zero_indexed_class_id = int( split_line[1] ) - 1
						tmp_string_data_list[ zero_indexed_class_id ].append( split_line[0] )
					else:
						image_pathname = line.strip()
						data_dict[ 'imagenames_list' ][ zero_indexed_class_id ].append( image_pathname )
					name_line = not name_line
				line_num += 1

		string_data = "\n"
		
		for i in range( num_classes ):
			print "generating matrix for class {}".format( i )
			#print "{}".format( tmp_string_data_list[i] )
			npmatr = np.genfromtxt( StringIO( string_data.join( tmp_string_data_list[i] ) ) )
			data_dict[ 'data_list' ].append( npmatr )

		# Can the class names be interpolated?
		tmp_vals = []
		for class_index in range( num_classes ):
			m = re.search( r'(\d*\.?\d+)', data_dict[ 'classnames_list' ][class_index] )
			if m:
				tmp_vals.append( float( m.group(1) ) )
			else:
				tmp_vals = None
				break
		if tmp_vals:
			data_dict[ 'interpolation_coefficients' ] = tmp_vals

		# Instantiate the class
		the_training_set = cls( data_dict )

		# normalize the features
		#the_training_set.Normalize()
		# no wait, don't normalize until we feature reduce!
		
		return the_training_set

  #=================================================================================
	@classmethod
	def NewFromSignature( cls, signature, ts_name = "TestSet", ):
		"""@brief Creates a new TrainingSet from a single signature
		Was written with performing a real-time classification in mind.
		"""

		try:
			signature.is_valid()
		except:
			raise

		new_ts = cls()
		new_ts.source_path = ts_name
		new_ts.num_classes = 1
		new_ts.num_features = len( signature.feature_values )
		new_ts.num_images = 1
		new_ts.classnames_list.append( "UNKNOWN" )
		new_ts.featurenames_list = signature.names
		new_ts.imagenames_list.append( [ inputimage_filepath ] )
		numpy_matrix = np.array( signature.values )
		new_ts.data_list.append( numpy_matrix )

		return new_ts

  #=================================================================================
	@classmethod
	def NewFromDirectory( cls, top_level_dir_path, feature_set = "large", write_sig_files_todisk = True ):
		"""
		@brief A quick and dirty implementation of the wndchrm train command
		Build up the self.imagenames_list, then pass it off to a sig classifier function
		"""
		print "Creating Training Set from directories of images {}".format( top_level_dir_path )
		if not( os.path.exists( top_level_dir_path ) ):
			raise ValueError( 'Path "{}" doesn\'t exist'.format( top_level_dir_path ) )
		if not( os.path.isdir( top_level_dir_path ) ):
			raise ValueError( 'Path "{}" is not a directory'.format( top_level_dir_path ) )

		num_images = 0
		num_classes = 0
		classnames_list = []
		imagenames_list = []

		for root, dirs, files in os.walk( top_level_dir_path ):
			if root == top_level_dir_path:
				if len( dirs ) <= 0:
					# no class structure
					file_list = []
					for file in files:
						if '.tif' in file:
							file_list.append( os.path.join( root, file ) )
					if len( file_list ) <= 0:
						# nothing here to process!
						raise ValueError( 'No tiff files in directory {}'.format( root ) )
					classnames_list.append( root )
					num_classes = 1
					num_images = len( file_list )
					imagenames_list.append( file_list )
					break
			else:
				file_list = []
				for file in files:
					if '.tif' in file:
						file_list.append( os.path.join( root, file ) )
				if len( file_list ) <= 0:
					# nothing here to process!
					continue
				# this class's name will be "subdir" in /path/to/topleveldir/subdir
				root, dirname = os.path.split( root )
				classnames_list.append( dirname )
				num_images += len( file_list )
				num_classes += 1
				imagenames_list.append( file_list )

		if num_classes <= 0:
			raise ValueError( 'No valid images or directories of images in this directory' )

		# instantiate a new training set
		new_ts = cls()
		new_ts.num_images = num_images
		new_ts.num_classes = num_classes
		new_ts.classnames_list = classnames_list
		new_ts.imagenames_list = imagenames_list
		new_ts.source_path = top_level_dir_path
		new_ts._ProcessSigCalculationSerially( feature_set, write_sig_files_todisk )
		if feature_set == "large":
			# FIXME: add other options
			new_ts.feature_options = "-l"
		return new_ts

  #=================================================================================
	@classmethod
	def NewFromFileOfFiles( cls, fof_path, feature_set = "large", write_sig_files_todisk = True ):
		"""FIXME: Implement!"""
		pass

  #=================================================================================
	@classmethod
	def NewFromSQLiteFile(cls, path):
		"""FIXME: Implement!"""
		pass

  #=================================================================================
	def _ProcessSigCalculationSerially( self, feature_set = "large", write_sig_files_to_disk = True, options = None ):
		"""
		Work off the self.imagenames_list
		"""
		# FIXME: check to see if any .sig, or .pysig files exist that match our
		#        Signature calculation criteria, and if so read them in and incorporate them

		sig = None
		class_id = 0
		for class_filelist in self.imagenames_list:
			for sourcefile in class_filelist:
				if feature_set == "large":
					sig = Signatures.LargeFeatureSet( sourcefile, options )
				elif feature_set == "small":
					sig = Signatures.SmallFeatureSet( sourcefile, options )
				else:
					raise ValueError( "sig calculation other than small and large feature set hasn't been implemented yet." )
				# FIXME: add all the other options
				# check validity
				sig.is_valid()
				if write_sig_files_to_disk:
					sig.WriteFeaturesToASCIISigFile()
				self.AddSignature( sig, class_id )
			class_id += 1


  #=================================================================================
	def _ProcessSigCalculationParallelly( self, feature_set = "large", write_sig_files_todisk = True ):
		"""
		FIXME: When we figure out concurrency
		"""
		pass

  #=================================================================================
	def Normalize( self, test_set = None ):
		"""
		By convention, the range of values are normalized on an interval [0,100]
		FIXME: edge cases, clipping, etc
		"""

		if not( self.normalized_against ):

			full_stack = np.vstack( self.data_list )
			total_num_imgs, num_features = full_stack.shape
			self.feature_maxima = [None] * num_features
			self.feature_minima = [None] * num_features

			for i in range( num_features ):
				feature_max = np.max( full_stack[:,i] )
				self.feature_maxima[ i ] = feature_max
				feature_min = np.min( full_stack[:,i] )
				self.feature_minima[ i ] = feature_min
				for class_matrix in self.data_list:
					class_matrix[:,i] -= feature_min
					class_matrix[:,i] /= (feature_max - feature_min)
					class_matrix[:,i] *= 100
			self.normalized_against = "itself"

		if test_set:

			# sanity checks
			if test_set.normalized_against:
				raise ValueError( "Test set {} has already been normalized against {}."\
						.format( test_set.source_path, test_set.normalized_against ) )
			if test_set.featurenames_list != self.featurenames_list:
				raise ValueError("Can't normalize test_set {} against training_set {}: Features don't match."\
						.format( test_set.source_path, self.source_path ) )

			for i in range( test_set.num_features ):
				for class_matrix in test_set.data_list:
					class_matrix[:,i] -= self.feature_minima[i]
					class_matrix[:,i] /= (self.feature_maxima[i] - self.feature_minima[i])
					class_matrix[:,i] *= 100

			test_set.normalized_against = self.source_path
			

  #=================================================================================
	def FeatureReduce( self, requested_features ):
		"""
		Returns a new TrainingSet that contains a subset of the features
		arg requested_features is a tuple of features
		the returned TrainingSet will have features in the same order as they appear in
		     requested_features
		"""

		# Check that self's faturelist contains all the features in requested_features

		selfs_features = set( self.featurenames_list )
		their_features = set( requested_features )
		if not their_features <= selfs_features:
			missing_features_from_req = their_features - selfs_features
			err_str = error_banner + "Feature Reduction error:\n"
			err_str += "The training set '{}' is missing ".format( self.source_path )
			err_str += "{}/{} features that were requested in the feature reduction list.".format(\
					len( missing_features_from_req ), len( requested_features ) )
			err_str += "\nDid you forget to convert the feature names into their modern counterparts?"

			raise ValueError( err_str )

		# copy everything but the signature data
		reduced_ts = TrainingSet()
		reduced_ts.source_path = self.source_path + "(feature reduced)"
		reduced_ts.num_classes = self.num_classes
		assert reduced_ts.num_classes == len( self.data_list )
		new_num_features = len( requested_features )
		reduced_ts.num_features = new_num_features
		reduced_ts.num_images = self.num_images
		reduced_ts.imagenames_list = self.imagenames_list[:] # [:] = deepcopy
		reduced_ts.classnames_list = self.classnames_list[:]
		reduced_ts.featurenames_list = requested_features[:]
		reduced_ts.interpolation_coefficients = self.interpolation_coefficients[:]
		reduced_ts.feature_maxima = [None] * new_num_features
		reduced_ts.feature_minima = [None] * new_num_features

		# copy feature minima/maxima
		if self.feature_maxima and self.feature_minima:
			new_index = 0
			for featurename in requested_features:
				old_index = self.featurenames_list.index( featurename )
				reduced_ts.feature_maxima[ new_index ] = self.feature_maxima[ old_index ]
				reduced_ts.feature_minima[ new_index ] = self.feature_minima[ old_index ]
				new_index += 1

		# feature reduce
		for fat_matrix in self.data_list:
			num_imgs_in_class, num_old_features = fat_matrix.shape
			# NB: double parentheses required when calling numpy.zeros(), i guess it's a tuple thing
			new_matrix = np.zeros( ( num_imgs_in_class, new_num_features ) )
			new_column_index = 0
			for featurename in requested_features:
				fat_column_index = self.featurenames_list.index( featurename )
				new_matrix[:,new_column_index] = fat_matrix[:,fat_column_index]
				new_column_index += 1
			reduced_ts.data_list.append( new_matrix )

		return reduced_ts

  #=================================================================================
	def AddSignature( self, signature, class_id_index = None ):
		"""
		@argument signature is a valid signature
		@argument class_id_index identifies the class to which the signature belongs
		"""
		
		if (self.data_list == None) or ( len( self.data_list ) == 0 ) :
			# If no class_id_index is specified, sig goes in first matrix in the list by default
			# make sure there's something there when you try to dereference that index
			self.data_list = []
			self.data_list.append( None )

			self.featurenames_list = signature.names
			self.num_features = len( signature.names )
		else:
			if not( self.featurenames_list == signature.names ):
				raise ValueError("Can't add the signature '{}' to training set because it contains different features.".format( signature.path_to_image_file ) )

		# signatures may be coming in out of class order
		while (len( self.data_list ) - 1) < class_id_index:
			self.data_list.append( None )

		if self.data_list[ class_id_index ] == None:
			self.data_list[ class_id_index ] = np.array( signature.values )
		else:
			# vstack takes only one argument, a tuple, thus the extra set of parens
			self.data_list[ class_id_index ] = np.vstack( ( self.data_list[ class_id_index ] ,\
					np.array( signature.values ) ) )


  #=================================================================================
	def CalculateFisherScores( self ):
		"""
		FIXME: implement!
		"""
		pass

  #=================================================================================
	def PickleMe( self, pathname = None ):
		"""
		FIXME: pathname needs to end with suffix '.fit.pickled'
		       or TrainingSet.FromPickleFile() won't read it.
		"""

		outfile_pathname = ""
		if pathname != None:
			outfile_pathname = pathname
		else:
			# try to generate a path based on member source_path
			if self.source_path == None or self.source_path == "":
				raise ValueError( "Can't pickle this training set: its 'source_path' member"\
						"is not defined, and you did not specify a file path for the pickle file." )
			if os.path.isdir( self.source_path ):
				# this trainingset was generated from a directory
				# naming convention is /path/to/topleveldir/topleveldir-options.fit.pickled
				root, top_level_dir = os.path.split( self.source_path )
				if self.feature_options != None and self.feature_options != "":
					outfile_pathname = os.path.join( self.source_path, \
							                  top_level_dir + self.feature_options + ".fit.pickled" )
				else:
					outfile_pathname = os.path.join( self.source_path, \
					                      top_level_dir + ".fit.pickled" )
			else:
				# was genearated from a file, could have already been a pickled file
				if self.source_path.endswith( "fit.pickled" ):
					outfile_pathname = self.source_path
				elif self.source_path.endswith( ".fit" ):
					outfile_pathname = self.source_path + ".pickled"
				else:
					outfile_pathname = self.source_path + ".fit.pickled"	

		if os.path.exists( outfile_pathname ):
			print "Overwriting {}".format( outfile_pathname )
		else:
			print "Writing {}".format( outfile_pathname )
		with open( outfile_pathname, 'wb') as outfile:
			pickle.dump( self.__dict__, outfile, pickle.HIGHEST_PROTOCOL )


	def DumpNumpyArrays():
		pass
# END TrainingSet class definition


######################################################################################
# GLOBAL FUNCTIONS
######################################################################################

def WeightedNeighborDistance5( trainingset, testimg, feature_weights ):
	"""
	If you're using this function, your training set data is not continuous
	for N images and M features:
	  trainingset is list of length L of N x M numpy matrices
	  testtile is a 1 x M list of feature values
	NOTE: the trainingset and test image must have the same number of features!!!
	AND: the features must be in the same order!!
	Returns a tuple with norm factor and list of length L of marginal probabilities
	FIXME: what about tiling??
	"""

	#print "classifying..."
	epsilon = np.finfo( np.float ).eps

	num_features_in_testimg = len( testimg ) 
	weights_squared = np.square( feature_weights )

	# initialize
	class_similarities = [0] * trainingset.num_classes

	for class_index in range( trainingset.num_classes ):
		#print "Calculating distances to class {}".format( class_index )
		num_tiles, num_features = trainingset.data_list[ class_index ].shape
		assert num_features_in_testimg == num_features,\
		"num features {}, num features in test img {}".format( num_features, num_test_img_features )

		# create a view
		sig_matrix = trainingset.data_list[ class_index ]
		wnd_sum = 0
		num_collisions = 0

		#print "num tiles: {}, num_test_img_features {}".format( num_tiles, num_test_img_features )
		for tile_index in range( num_tiles ):
			#print "{} ".format( tile_index )
			# epsilon checking for each feature is too expensive
			# do this quick and dirty check until we can figure something else out
			dists = np.absolute( sig_matrix[ tile_index ] - testimg )
			w_dist = np.sum( dists )
			if w_dist < epsilon:
				num_collisions += 1
				continue
			dists = np.multiply( weights_squared, np.square( dists ) )
			w_dist = np.sum( dists )
			# The exponent -5 is the "5" in "WND5"
			class_similarities[ class_index ] += w_dist ** -5
		#print "\n"

		class_similarities[ class_index ] /= ( num_tiles - num_collisions )

	normalization_factor = sum( class_similarities )

	return ( normalization_factor, [ x / normalization_factor for x in class_similarities ] ) 

#=================================================================================
def ClassifyTestSet( training_set, test_set, feature_weights ):
	"""
	@remarks - all three input arguments must have the same number of features,
	and in the same order for this to work properly
	FIXME: What happens when the ground truth is not known? Currently they would all be shoved
	       into class 1, might not be a big deal since class name should be something
	       like "UNKNOWN"
	FIXME: return some python construct that contains classification results
	"""

	train_set_len = len( training_set.featurenames_list )
	test_set_len = len( test_set.featurenames_list )
	feature_weights_len = len( feature_weights.names )

	if train_set_len != test_set_len or \
	   train_set_len != feature_weights_len or \
	   test_set_len  != feature_weights_len:
		raise ValueError( "Can't classify: one or more of the inputs has a different number of" \
				"features than the others: training set={}, test set={}, feature weights={}".format( \
				train_set_len, test_set_len, feature_weights_len ) + ". Perform a feature reduce." )

	print "Classifying test set '{}' ({} features) against training set '{}' ({} features)".\
	      format( test_set.source_path, test_set_len, training_set.source_path, train_set_len )

	column_header = "image\tnorm. fact.\t"
	column_header +=\
			"".join( [ "p(" + class_name + ")\t" for class_name in training_set.classnames_list ] )

	column_header += "act. class\tpred. class\tpred. val."
	print column_header

	interp_coeffs = None
	if training_set.interpolation_coefficients:
		interp_coeffs = np.array( training_set.interpolation_coefficients )

	for test_class_index in range( test_set.num_classes ):
		num_class_imgs, num_class_features = test_set.data_list[ test_class_index ].shape
		for test_image_index in range( num_class_imgs ):
			one_image_features = test_set.data_list[ test_class_index ][ test_image_index,: ]
			normalization_factor, marginal_probabilities = \
					WeightedNeighborDistance5( training_set, one_image_features, feature_weights.values )

			# FIXME: call PrintClassificationResultsToSTDOUT( results )
			# img name:
			output_str = test_set.imagenames_list[ test_class_index ][ test_image_index ]
			# normalization factor:
			output_str += "\t{val:0.3g}\t".format( val=normalization_factor )
			# marginal probabilities:
			output_str += "".join(\
					[ "{val:0.3f}".format( val=prob ) + "\t" for prob in marginal_probabilities ] )
			output_str += test_set.classnames_list[ test_class_index ] + "\t"
			# actual class:
			output_str += test_set.classnames_list[ test_class_index ] + "\t"
			# predicted class:
			marg_probs = np.array( marginal_probabilities )
			output_str += "{}\t".format( training_set.classnames_list[ marg_probs.argmax() ] )
			# interpolated value, if applicable
			if interp_coeffs is not None:
				interp_val = np.sum( marg_probs * interp_coeffs )
				output_str += "{val:0.3f}".format( val=interp_val )
			print output_str

#=================================================================================
def PrintClassificationResultsToSTDOUT( result ):
	"""
	FIXME: Implement!
	"""
	pass

#============================================================================
def UnitTest1():
	
	weights_filepath = '/Users/chris/projects/josiah_worms_subset/josiah_worms_subset.fisher_weights'

	weights = FeatureWeights.NewFromFile( weights_filepath )
	weights.EliminateZeros()
	weights.names = FeatureNameMap.TranslateToNewStyle( weights.names )

	#big_ts = TrainingSet.NewFromFitFile( '/Users/chris/projects/josiah_worms_subset/trunk_train.fit' )
	#big_ts.PickleMe()
	big_ts = TrainingSet.NewFromPickleFile( '/Users/chris/projects/josiah_worms_subset/trunk_train.fit.pickled' )
	big_ts.featurenames_list = FeatureNameMap.TranslateToNewStyle( big_ts.featurenames_list )

	reduced_ts = big_ts.FeatureReduce( weights.names )
	reduced_ts.Normalize()
	
	ClassifyTestSet( reduced_ts, reduced_ts, weights )

#=========================================================================
def UnitTest2():

	ts = TrainingSet.NewFromDirectory( '/Users/chris/projects/josiah_worms_subset',\
	                                   feature_set = "large" )
	ts.PickleMe()
	
#================================================================
def UnitTest3():

	path = "Y24-2-2_GREEN.tif"
	sigs = Signatures.LargeFeatureSet( path )
	sigs.WriteFeaturesToASCIISigFile( "pychrm_calculated.sig" )

initialize_module()

#================================================================
if __name__=="__main__":
	
	UnitTest1()
	# UnitTest2()
	# UnitTest3()
	# pass
