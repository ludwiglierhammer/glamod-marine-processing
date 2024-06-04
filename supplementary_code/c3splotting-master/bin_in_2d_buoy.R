
bin.in.2d.buoy <- function ( data2bin, xbin = c(-180,180,1), ybin = c(-90,90,1) ) {

as.numeric.factor <- function(x) {as.numeric(levels(x))[x]}

colnames(data2bin)<-c("X","Y")
nbins.x <- ceiling((xbin[2]-xbin[1])/xbin[3])
nbins.y <- ceiling((ybin[2]-ybin[1])/ybin[3])
x.bin <- seq(from=xbin[1],to=xbin[2],by=xbin[3])
y.bin <- seq(from=ybin[1],to=ybin[2],by=ybin[3])

freq <-  as.data.frame(table(findInterval(data2bin$X, x.bin),
		findInterval(data2bin$Y, y.bin )))

freq<-freq[which(freq[,3] > 0 ),]
freq[,1] <- x.bin[as.numeric.factor(freq[,1])]
freq[,2] <- y.bin[as.numeric.factor(freq[,2])]
colnames(freq)<-c("X","Y","freq")

return(freq)
}
