#! /bin/bash

callerDir=$(pwd)
# Returns the directory the script exists in, no matter where it was called from.
scriptDir=$(cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd)
rootDir=$(cd "${scriptDir}/.." || exit; pwd)

configFile=${1:-"templates-beta.json"}

cd $scriptDir || exit

if [ ! -f "$configFile" ]; then
  echo "Configuration file '$configFile' does not exist!"; exit 1;
fi

tempFolder="${scriptDir}/temp"
zipsFolder="${tempFolder}/zips"

# Makes sure the temp folder is empty.
rm -rf "${tempFolder:?}"

mkdir "${tempFolder}"
mkdir "${zipsFolder}"

templatesBundlePath="${tempFolder}/action-templates.zip"
templatesMetadataPath="${tempFolder}/action-templates.yaml"

# Removes artifacts if already exist, to make sure they will be recreated properly.
rm -f $templatesBundlePath
rm -f $templatesMetadataPath

config=$(cat $configFile)

templatesCount=$(jq ".templates | length" <<< $config)

# Moves to packaging/temp/zips.
cd $zipsFolder || exit

metadataTemplatesEntries=()
hashes=""

for ((i=0; i<$templatesCount; i++)); do
  id=$(jq -r ".templates[${i}].id" <<< $config)
  name=$(jq -r ".templates[${i}].name" <<< $config)
  desc=$(jq -r ".templates[${i}].desc" <<< $config)

  zipPath="${zipsFolder}/${id}.zip"

  metadataTemplatesEntries+=("    ${id}: ${name} - ${desc}")

  sourceFolder="${rootDir}/${id}"

  # Moves to current template directory, to make sure we only zip given directory,
  # instead of entire path.
  cd $sourceFolder || exit


  zip -rq $zipPath "."

  # Since the final output is a zip containing other zip files, we cannot reliably
  # get a hash of it (as it will contain timestamps and other metadata of internal zip files).
  # Therefore, we calculate hash for each particular zip's content, and then we calculate a single
  # hash based on the individual ones.
  hashes="${hashes}$(unzip -p $zipPath | shasum -a 256 | awk '{print $1}')"
done

# Moves to zips directory, to make a bundle from all of the zipped templates.
cd $zipsFolder || exit

zip -rq $templatesBundlePath "."

hash=$(echo -n $hashes | shasum -a 256 | awk '{print $1}')
bundleUrl=$(jq ".templateBundleUrl" <<< $config)
date=$(date '+%Y-%m-%d')

touch $templatesMetadataPath

printf "hash: ${hash}\nurl: ${bundleUrl}\ndate: ${date}\ntemplates:\n" >> $templatesMetadataPath

for entry in "${metadataTemplatesEntries[@]}"; do
  printf "${entry}\n" >> $templatesMetadataPath
done

echo "Created Template Actions bundle with metadata:"
echo "--------------------------------------"
cat $templatesMetadataPath

cd $callerDir || exit
