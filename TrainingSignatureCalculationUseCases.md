# Introduction #

The following document applies to the eigen\_sample\_mat branch, upon which a significant amount of development is being made related to fine tuning which features are calculated. It is a document meant for wndcharm developers. It is meant to try to list all the possible scenarios from which precomputed signatures can be reused. This includes future plans to incorporate the saving of feature data into a database such as SQLite.

During the wndcharm train phase, signatures for images are calculated. Which signatures to be calculated depends on which image descriptor algorithms have been registered. The registration happens pre-main at run time. Wndcharm developers who want to incorporate another algorithm should create a class that inherits from the BaseAlgorithm class and call the compiler macro WC\_REGISTER\_ALGORITHM( ... ).

The complete list of all available image decomposition algorithms and all available image transforms upon which to calculate the image decomposition algorithms is saved in the FeatureNames singleton object.

The following is an attempt to handle the various signature procurement scenarios in the most efficient, fast, and general way.

# Definitions #

  * Let S = the small feature set of 1025 features
  * Let L = the large feature set of 2873 features
  * S is a subset of L
  * Let A = all the features known to wndcharm at runtime
  * S and L are subsets of A
  * Let O = some set of features that defined by the user or defined programmatically, and all the features in set O are known to wndcharm, therefore,
  * O is a subset of A
  * Let Q = some set of features defined by the user or otherwise that includes features that may or may not be known to wndcharm at runtime, and therefore,
  * Q is not a subset of A
  * Let N represent an empty set of features.
  * Let I = the full set of images that the user request signatures to be calculated

# Scenarios #

  * The "phonebook" FeatureNames singleton shall contain an ORDERED MAP of all features in the known universe, including the features it knows how to calculate, AND ALSO those it doesn't not know how to calculate, but it has observed through reading in signature information generated externally. The keys will be a string, and the value will be a FeatureNames pointer to the FeatureNames object containing references to the algorithm used, the index of the feature within the algorithm, and the ordered list of transforms used to create it. Technically, the keys here will always be unique, but the values may not.

  * User requests that a certain set of signatures be calculated for a specified set of features (S, L, A, O, Q) for some image set I. Let the requested set of features = R. Some of those features may have been pre-calculated and saved in a .sig file, or within a database (S, L, A, O, Q, N). Let the pre-calculated set of features = P.

  * R will be sorted. P may be, but is not necessarily sorted.

  1. Best case scenario: for a given image, P exactly equals R (implies order is the same). Outcome: blind reading in of values from source into memory via some dumb for loop. Would be useful to have or obtain some metadata on P, e.g., saving it somewhere in the file that P = S or L.
  1. P = R, but not in the correct order. In which case, P must be read in from sig file and placed into a std::set, and the std::set of P should be compared to the std::set of R.
  1. P may be a superset of R, e.g., when R is S and P is L. Read P into a std::map with FeatureName and value, generate a std::set of just the keys of said map, and use the std::set to derive the intersection. The values of the intersection set will then be loaded in the correct order into the Eigen::VectorXd.
  1. P may be a subset of R. Read P into a std::map with FeatureName and value, generate a std::set of just the keys of said map, and use the std::set to derive the difference. The `std::set<FeatureName*>` difference will be sent to A `SignatureCalculator` which will calculate the features based on the FeatureName pointer. The SignatureCalculator will return a std::map of `FeatureNames*` keys and calculated values, the values of which will be loaded into the Eigen::VectorXd.

  * It doesn't look like there's a built-in way to ask a std::map for a std::set of just its keys, so it's a design decision whether to simultaneously populate a separate std::set of just FeatureNames pointers while loading the map of `FeatureName*` and feature vals, or to extend the std::map class to implement a `keys()` function.

  * It also doesn't look like there's a built in way to compare two std::sets together to see if their equal. There should be some utility call that compares two vectors of features, like int `compare_feature_vectors(std::set<FeatureNames*> A, std::set<FeatureNames*> B)`, returning -1 if A is a subset of B, 0 if A == B and 1 if A is a superset of B, with optional arguments to get the intersection or difference.

# To-do #

  * Each instance of a FeatureName object should be unique. Their creation should be restricted (in c++ terms their constructor should be protected or private.)