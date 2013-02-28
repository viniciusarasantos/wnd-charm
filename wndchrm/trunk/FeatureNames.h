#ifndef __FEATURE_NAMES_H__
#define __FEATURE_NAMES_H__

#include "FeatureAlgorithms.h"
#include "ImageTransforms.h"
#include <stdio.h> // for sprintf
#include <string>
#include <vector>
#include <map>
#include <set>

/*
map and unordered_map comparison:
std::tr1::unordered_map:
       +parse    502400 lookups         0 misses      0.46 secs,   1091977 lookups/sec
       -parse    502400 lookups    502400 misses       2.2 secs,    229342 lookups/sec
std::map:
       +parse    502400 lookups         0 misses      0.82 secs,    610048 lookups/sec
       -parse    502400 lookups    502400 misses       2.4 secs,    205706 lookups/sec
*/

// defines OUR_UNORDERED_MAP based on what's available
#include "unordered_map_dfn.h"


class FeatureNames {
public:
/////////////////////////////////
//         Channels
/////////////////////////////////
// Instead of a string, this should be a channel object
	struct Channel {
		std::string name;

		Channel (const std::string &s) { name = s;}
		Channel (const char *s) { name = s;}
	};
// This just returns the string, should return a channel object by string lookup
	static const Channel *getChannelByName (const std::string &name);


/////////////////////////////////
//         Transforms
/////////////////////////////////
// Instead of a string, this should be a transform object with an execute() method
// The ImageTransform class is defined in a separate file ImageTransformss.h
	static const ImageTransform *getTransformByName (const std::string &name);
	static bool registerImageTransform (const ImageTransform *algorithm);


/////////////////////////////////
//      Feature Algorithms
/////////////////////////////////
// These represent a feature algorithm independently of any preceding transforms
// The FeatureAlgorithm class is defined in a separate file FeatureAlgorithms.h
	static const FeatureAlgorithm *getFeatureAlgorithmByName (const std::string &name);
	static const FeatureAlgorithm *getFeatureAlgorithmByName (const char * name) {return getFeatureAlgorithmByName (std::string (name)); };
	static bool registerFeatureAlgorithm (const FeatureAlgorithm *algorithm);


/////////////////////////////////
//        Feature Groups
/////////////////////////////////
// These represent the outputs of a feature algorithm together with all of its transforms
	struct FeatureGroup {
		std::string name;
		const FeatureAlgorithm *algorithm;
		const Channel *channel;
		std::vector<ImageTransform const *> transforms; // these are in order of application
		std::vector<std::string> labels;

		FeatureGroup () : algorithm(NULL), channel(NULL) {};
		FeatureGroup (const std::string &s, const FeatureAlgorithm *f, const Channel *c, std::vector<ImageTransform const *> &t) {
			name = s; algorithm = f; channel = c; transforms = t;
			if (algorithm)
				for (int i = 0; i < algorithm->n_features; i++) {
					char buf[16];
					sprintf (buf, " [%d]",i);
					labels.insert (labels.end(), name + buf);
				}
		};
	};
// This will store a new group if the name doesn't exist.
	static const FeatureGroup *getGroupByName (const std::string &name);


/////////////////////////////////
//          Features
/////////////////////////////////
	struct FeatureInfo {
		std::string name;
		const FeatureGroup *group;
		int index; // within group

		FeatureInfo () : name (""), group(NULL), index(-1) {};
		FeatureInfo (const std::string &s, const FeatureGroup *g, int i) { name = s; group = g; index = i;}
	};
	static const FeatureInfo *getFeatureInfoByName (const std::string &featurename_in);

/////////////////////////////////
// Old-style feature name lookup
/////////////////////////////////
	static const std::string &oldFeatureNameLookup (const std::string &featurename_in);


/////////////////////////////////
// pre-main initializers
/////////////////////////////////
	static const bool initialized();

private:
////////////////////////////////////////
// Private static object caches
////////////////////////////////////////
// Why are these maps to pointers?
// Can't store references because of how maps work. 
// Can't store the actual FeatureAlgorithm instance that was instantiated, have to make a copy, which causes a new registration, etc.
// Why are these declared as static functions with static variables inside?
// This is to avoid the "static initialization order fiasco" (see http://www.parashift.com/c++-faq/static-init-order-on-first-use-members.html)
	typedef OUR_UNORDERED_MAP<std::string, const Channel *> cnm_t;
	static cnm_t &channels_map ();

	typedef OUR_UNORDERED_MAP<std::string, const ImageTransform *> tnm_t;
	static tnm_t &transforms_map ();

	typedef OUR_UNORDERED_MAP<std::string, const FeatureAlgorithm *> fam_t;
	static fam_t &feature_algorithms_map ();

	typedef OUR_UNORDERED_MAP<std::string, const FeatureGroup *> fgnm_t;
	static fgnm_t &feature_groups_map ();

	typedef OUR_UNORDERED_MAP<std::string, const FeatureInfo *> fnm_t;
	static fnm_t &feature_names_map ();

	typedef OUR_UNORDERED_MAP<std::string, std::string> ofnm_t;
	static ofnm_t &old_features_map ();

	static const bool init_maps_;
	
};

#endif // __FEATURE_NAMES_H__