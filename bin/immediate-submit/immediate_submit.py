#!/usr/bin/env python3
# this script is used to submit batch jobs for indivdiual snakemake rules to SLURM, SGE or TORQUE clusters.
# written by Philipp Resl

import os
import sys
import shutil

from snakemake.utils import read_job_properties

# last command-line argument is the job script
jobscript = sys.argv[-1]

# last but one argument is the submission system
subs = sys.argv[-2]
#print("---------------------------------------------------------------------", file=sys.stderr)
print("Command line arguments are: ", file=sys.stderr)
print(sys.argv, file=sys.stderr)
# check command-line arguments for dependencies
dependencies = ""
if subs == "slurm":
	dependencies = set(sys.argv[1:-2])
elif subs == "sge":
	dependencies = dependencies.join(sys.argv[1:-2])
elif subs == "torque":
	dependencies = dependencies.join(sys.argv[1:-2])
else:
	print("Cannot get dependencies for submission system")
	sys.exit(1)
# parse the job script for the job properties that are encoded by snakemake within
# this also includes the information contained in the cluster-config file as job_properties["cluster"]
job_properties = read_job_properties(jobscript)

print("Job submision for job:", job_properties["rule"], file=sys.stderr)
print("Submission system:", subs,file=sys.stderr)

#some output for debugging:
#print(job_properties, file=sys.stderr)
#print(job_properties["wildcards"], file=sys.stderr)
#print("Dependencies:", file=sys.stderr)
#print(dependencies, file=sys.stderr)
#print(sys.argv, file=sys.stderr)

#list of items recognized by the -l (resource) flag of qsub:
sge_resources=["nodes", "pmem", "vmem", "mem", "walltime", "h_vmem", "ppn"] #my need to be extended for different clusters


cmdline=[]
# create list with command line arguments
if subs == "slurm":
	cmdline = ["sbatch"]
	
	# TODO: figure out how to handle threading information more generally:
	if job_properties["threads"]:
		job_properties["cluster"]["cpus-per-task"] = job_properties["threads"]
	#job_properties["cluster"]["ntasks"] = job_properties["threads"]
	#job_properties["cluster"]["ntasks-per-node"] = job_properties["threads"]

	# get more informative job name based on wildcard values
	prefix = "-".join(job_properties["wildcards"].values())
	if prefix:
		job_properties["cluster"]["job-name"] = job_properties["cluster"]["job-name"]+"-"+prefix	
	
	# add additional slurm arguments from cluster config file 
	slurm_args = ""
	for element in job_properties["cluster"]:
		if element == "error" or element == "output":
			slurm_args += " --%s=%s" %(element, job_properties["cluster"][element].replace("slurm", "slurm-"+job_properties["cluster"]["job-name"]))
		else:
			slurm_args += " --%s=%s" %(element, job_properties["cluster"][element])
	
	# add information acquired so far to the sbatch command
	cmdline.append(slurm_args)
	
	# now work on dependencies
	print("\nDependencies for this job:", file=sys.stderr)
	if dependencies:
		cmdline.append(" --dependency")
		# only keep numbers (which are the jobids) in dependencies list. this is necessary because slurm returns more than the jobid. For other schedulers this could be different!
		dependencies = [x for x in dependencies if x.isdigit()]
		cmdline.append("afterok:" + ":".join(dependencies))
		print(dependencies, file=sys.stderr)
	else:
		print("none", file=sys.stderr)	
elif subs == "sge":
	# get more informative job name based on wildcard values
	prefix = "-".join(job_properties["wildcards"].values())
	if prefix:
		job_properties["cluster"]["N"] = job_properties["cluster"]["N"]+"-"+prefix
		# set name for cluster log files:
	job_properties["cluster"]["o"] = job_properties["cluster"]["o"].replace("%j",job_properties["cluster"]["N"])
	job_properties["cluster"]["e"] = job_properties["cluster"]["e"].replace("%j",job_properties["cluster"]["N"])

	cmdline = ["qsub"]
	
	# extract info an requested resources
	sge_args = "-cwd -V"
	
	if "pe" in job_properties["cluster"] and "nodes" in job_properties["cluster"]:
		print("WARNING: You have set pe and nodes in your cluster config file. Is this really what you want?", file=sys.stderr)

	for element in job_properties["cluster"]:
		#print(element, file=sys.stderr)
			
		#if element == "error" or element == "output":
		#	sge_args += " --%s=%s" %(element, job_properties["cluster"][element].replace("sge", "sge-"+job_properties["cluster"]["job-name"]))
		#else:
		#	sge_args += " --%s=%s" %(element, job_properties["cluster"][element])

		if element in sge_resources:
			if "nodes" == element: #special case when nodes are specified, in this case threads are ppns
				sge_args += " -l %s=%s:ppn=%s" % ("nodes", job_properties["cluster"]["nodes"], job_properties["threads"])
			else:			
				sge_args += " -l %s=%s" % (element, job_properties["cluster"][element])
		else:
			if element == "pe": # set parallel environment and correct number of threads according to config.yaml
				sge_args += " -pe %s %s" % (job_properties["cluster"]["pe"], job_properties["threads"])
			else:
				sge_args += " -%s %s" % (element, job_properties["cluster"][element])
	#job_properties["sge_resources"] = resources
	# TODO: add correct thread handling for SGE clusters
	#sge_args = "-cwd -V -q {queue} -l h_vmem={mem} -pe {pe} {ntasks} -o {output} -e {error} -N {N}".format(**job_properties["cluster"])	
	cmdline.append(sge_args)

	#now work on dependencies
	print("\nDependencies for this job:", file=sys.stderr)
	if dependencies:
		cmdline.append("-hold_jid")
		# only keep numbers (which are the jobids) in dependencies list. this is necessary because slurm returns more than the jobid. For other schedulers this could be different!
		dependencies = [x for x in dependencies.split(" ") if x.isdigit()]
		cmdline.append(",".join(dependencies))
		print(dependencies, file=sys.stderr)
	else:
		print("none", file=sys.stderr)	
	# add @:
	#cmdline.append("-@")
elif subs == "torque":
	#print("Job properties:", file=sys.stderr)
	#print(job_properties["cluster"], file=sys.stderr)
	# set informative job name:
	if "species" in job_properties["wildcards"]:
		name =  job_properties["cluster"]["N"] + "-" + job_properties["wildcards"]["species"]
	elif "busco" in job_properties["wildcards"]:
		name =  job_properties["cluster"]["N"] + "-" + job_properties["wildcards"]["busco"]
	else:
		name = job_properties["cluster"]["N"]
	job_properties["cluster"]["N"] = name
	# set name for cluster log files:
	prefix =  job_properties["rule"] + "-torque"
	job_properties["cluster"]["o"] = job_properties["cluster"]["o"].replace("slurm", prefix).replace("%j",name)
	job_properties["cluster"]["e"] = job_properties["cluster"]["e"].replace("slurm", prefix).replace("%j",name)
	cmdline = ["qsub"]
	
	# extract info an requested resources
	sge_args = "-w $(pwd) -V"
	
	if "pe" in job_properties["cluster"] and "nodes" in job_properties["cluster"]:
		print("WARNING: You have set pe and nodes in your cluster config file. Is this really what you want?", file=sys.stderr)

	for element in job_properties["cluster"]:
		#print(element, file=sys.stderr)
		
		#if element == "error" or element == "output":
		#	sge_args += " --%s=%s" %(element, job_properties["cluster"][element].replace("torque", "torque-"+job_properties["cluster"]["job-name"]))
		#else:
		#	sge_args += " --%s=%s" %(element, job_properties["cluster"][element])

		if element in sge_resources:
			if "nodes" == element: #special case when nodes are specified, in this case threads are ppns
				sge_args += " -l %s=%s:ppn=%s" % ("nodes", job_properties["cluster"]["nodes"], job_properties["threads"])
			else:			
				sge_args += " -l %s=%s" % (element, job_properties["cluster"][element])
		else:
			if element == "pe": # set parallel environment and correct number of threads according to config.yaml
				sge_args += " -pe %s %s" % (job_properties["cluster"]["pe"], job_properties["threads"])
			else:
				sge_args += " -%s %s" % (element, job_properties["cluster"][element])
	#job_properties["sge_resources"] = resources
	cmdline.append(sge_args)

	#now work on dependencies
	print("\nDependencies for this job:", file=sys.stderr)
	print(dependencies, file=sys.stderr)
	if dependencies:
		deps = "-W depend=afterok:"
		#cmdline.append("-W depend=afterok")
		# only keep numbers (which are the jobids) in dependencies list. this is necessary because slurm returns more than the jobid. For other schedulers this could be different!
		dependencies = [x for x in dependencies.split(" ") if x.isdigit()]
		deps += ":".join(dependencies)
		cmdline.append(deps)
		print(dependencies, file=sys.stderr)
		print(deps, file=sys.stderr)
	else:
		print("none", file=sys.stderr)	
	# add @:
	#cmdline.append("-@")
else:
	#print("Immediate submit error: Unkown submission system!")
	sys.exit(1)


cmdline.append(jobscript)


#now write final commandback to the system
print("\nSubmission command:", file=sys.stderr)
print(" ".join(cmdline), file=sys.stderr)
print
os.system(" ".join(cmdline))

print("---------------------------------------------------------------------", file=sys.stderr)
