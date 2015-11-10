Rally Style Commandments
========================

- Step 1: Read the OpenStack Style Commandments
  http://docs.openstack.org/developer/hacking/
- Step 2: Read on

Rally Specific Commandments
---------------------------
* [N30x] - Reserved for rules related to ``mock`` library
 * [N301] - Ensure that ``assert_*`` methods from ``mock`` library is used correctly
 * [N302] - Ensure that nonexistent "assert_called" is not used
 * [N303] - Ensure that  nonexistent "assert_called_once" is not used
* [N310-N314] - Reserved for rules related to logging
 * [N310] - Ensure that ``rally.common.log`` is used as logging module
 * [N311] - Validate that debug level logs are not translated
 * [N312] - Validate correctness of debug on check.
* [N32x] - Reserved for rules related to assert* methods
 * [N320] - Ensure that ``assertTrue(isinstance(A, B))``  is not used
 * [N321] - Ensure that ``assertEqual(type(A), B)`` is not used
 * [N322] - Ensure that ``assertEqual(A, None)`` and ``assertEqual(None, A)`` are not used
 * [N323] - Ensure that ``assertTrue/assertFalse(A in/not in B)`` are not used with collection contents
 * [N324] - Ensure that ``assertEqual(A in/not in B, True/False)`` and ``assertEqual(True/False, A in/not in B)`` are not used with collection contents
* [N340] - Ensure that we are importing always ``from rally import objects``
* [N341] - Ensure that we are importing oslo_xyz packages instead of deprecated oslo.xyz ones
* [N350] - Ensure that single quotes are not used
* [N351] - Ensure that data structs (i.e Lists and Dicts) are declared literally rather than using constructors
* [N352] - Ensure that string formatting only uses a mapping if multiple mapping keys are used.
* [N353] - Ensure that unicode() function is not uset because of absence in py3
