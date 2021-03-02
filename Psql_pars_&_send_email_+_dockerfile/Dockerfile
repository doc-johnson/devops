FROM alpine:3.12
RUN apk --no-cache add postgresql-client jq ssmtp
CMD [ "bash" ]


#cat > /etc/ssmtp/ssmtp.conf << EOF 
#root=postmaster
#mailhub=relay.zoloto585.int
#hostname=`hostname`
#FromLineOverride=YES
#EOF
