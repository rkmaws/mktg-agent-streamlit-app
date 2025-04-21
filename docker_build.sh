# Get AWS account ID and region from the specified profile
if [ -z "$1" ]
  then
    echo "No profile supplied"
    exit 1
fi
AWSAccountId=$(aws sts get-caller-identity --profile $1 --query Account --output text)
AWSRegion=$(aws configure get region --profile $1)
aws ecr get-login-password --profile $1 --region ${AWSRegion} | docker login --username AWS --password-stdin ${AWSAccountId}.dkr.ecr.${AWSRegion}.amazonaws.com
COMMIT_HASH=$(git rev-parse --short HEAD)
COMMIT_HASH=${COMMIT_HASH//./a}
echo $COMMIT_HASH
IMAGE_TAG=${!COMMIT_HASH:=latest}
echo $IMAGE_TAG
echo Build started on `date`
StreamlitImageRepo=streamlitdeploy-streamlitimagerepo-oqsv5e5d405g
# docker system prune -a
docker build --platform linux/amd64 -t ${StreamlitImageRepo} .
docker tag ${StreamlitImageRepo}:latest ${AWSAccountId}.dkr.ecr.${AWSRegion}.amazonaws.com/${StreamlitImageRepo}:$IMAGE_TAG
echo Build completed on `date`
docker push ${AWSAccountId}.dkr.ecr.${AWSRegion}.amazonaws.com/${StreamlitImageRepo}:$IMAGE_TAG
docker inspect ${StreamlitImageRepo}:latest | grep Architecture
