
bin.in.2d <- function ( data2bin, xbin = c(-180,180,1), ybin = c(-90,90,1) ) {

colnames(data2bin)<-c("X","Y")
nbins.x <- ceiling((xbin[2]-xbin[1])/xbin[3])
nbins.y <- ceiling((ybin[2]-ybin[1])/ybin[3])
x.bin <- seq(from=xbin[1],to=xbin[2],by=xbin[3])
y.bin <- seq(from=ybin[1],to=ybin[2],by=ybin[3])

padding1<-rep(seq(xbin[1]+0.5*xbin[3],xbin[2]-0.5*xbin[3],xbin[3]),times=nbins.y)
padding2<-rep(seq(ybin[1]+0.5*ybin[3],ybin[2]-0.5*ybin[3],ybin[3]),each=nbins.x)
padding<-cbind(padding1,padding2)
colnames(padding)<-c("X","Y")

tmp.data<-as.data.frame(rbind(data2bin,padding))
colnames(tmp.data)<-c("X","Y")

freq <-  as.data.frame(table(findInterval(tmp.data$X, x.bin),
		findInterval(tmp.data$Y, y.bin )))

freq[,1] <- as.numeric(freq[,1])
freq[,2] <- as.numeric(freq[,2])

freq2D <- matrix(nrow=nbins.x,ncol=nbins.y)*0
freq2D[cbind(freq[,1], freq[,2])] <- freq[,3]
freq2D<-freq2D-1

return(freq2D)
}
