# Introduction #



# Details #

```
#!/usr/bin/env python

# Pull the input image's filename from the command line
import sys
input_filename = sys.argv[1]

# import pychrm
from pychrm.TrainingSet import *

from_scratch = False

if from_scratch:
	# I preprocessed your training set and feature weights and pickled them for speed.
	# Pickle files are binary files that are super fast to load.
	# You don't need to use a pickle file though, you can make one from scratch
	# Here's how:
	 
	# 1. Load the raw c-charm fit file
	full_training_set = DiscreteTrainingSet.NewFromFitFile( "OfficialState.fit" )

	# 2. C-charm uses "Lior-style" feature names. Translate them into the new "Ilya-style"
	full_training_set.featurenames_list = FeatureNameMap.TranslateToNewStyle( full_training_set.featurenames_list )

	# 3. Normalize the features:
	full_training_set.Normalize()

	# 4. Make Fisher scores based on the normalized training set
	full_fisher_weights = FisherFeatureWeights.NewFromTrainingSet( full_training_set )

	# 5. Take only the top 200 features
	reduced_fisher_weights = full_fisher_weights.Threshold( 200 )

	# 6. Reduce the training set feature space to contain only those top 200 features
	reduced_training_set = full_training_set.FeatureReduce( reduced_fisher_weights.names )

	# 7. Save your work:
	reduced_training_set.PickleMe( "OfficialState_normalized_200_features.fit.pickled" )
	reduced_fisher_weights.PickleMe( "feature_weights_len_200.weights.pickled" )


# But I've already done all that, just proceed from here:
reduced_training_set = DiscreteTrainingSet.NewFromPickleFile( "OfficialState_normalized_200_features.fit.pickled" )
reduced_fisher_weights = FisherFeatureWeights.NewFromPickleFile( "feature_weights_len_200.weights.pickled" )


# Calculate features for the test image, but only those features we need
test_image_signatures = Signatures.NewFromFeatureNameList( input_filename, reduced_fisher_weights.names )

# It might be useful to hold onto the sigs, so write them out to a file
test_image_signatures.WriteFeaturesToASCIISigFile()

# In the future, if you want to load the sig file, use this function call:
future = False
if future:
	test_image_signatures = Signatures.NewFromSigFile( "whatever_the_path_is.sig" )
# Note if pychrm created the sig file it will have an extension of ".pysig" so use that

# Normalize the newly calculated signatures against the training set
test_image_signatures.Normalize( reduced_training_set )

# Classify away! Return all the pertinent results including marginal probabilities,
# normalization factor, and interpolated value inside the variable "result"
result = DiscreteImageClassificationResult.NewWND5( reduced_training_set, reduced_fisher_weights, test_image_signatures )

# In this specific use case, Mark identifies state membership by comparing the interpolated value
# against age score value "bin walls" that he defined empirically.

if result.predicted_value >= 1 and result.predicted_value <= 1.2:
	print "\n****** PYCHRM SEZ THIS IS A STATE 1 PHARYNX!"
elif result.predicted_value >= 1.8 and result.predicted_value <= 2.2:
	print "\n****** PYCHRM SEZ THIS IS A STATE 2 PHARYNX!"
else:
	print "\n****** PYCHRM SEZ THIS IS A GAPPER PHARYNX!"
```