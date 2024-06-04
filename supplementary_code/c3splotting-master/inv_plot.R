inv_plot <- function (level=0, data, dck.want, sid.want=NA, dev="pdf", pdfname="tmp.pdf") {

  print.comm<-F

  cman.dck<-c(795,895,995)
  moor.dck<-c(143,144,145,146,793,seq(876,883),893,993,994)

  if(!exists("add_date2", mode = "function")) source("inv_plot_func.R")

   sid.list<-read.delim('sid_list.txt',sep = "\t",header=FALSE)
   names(sid.list)<-c("sid","description")
   dck.list<-read.delim('dck_list.txt',sep = "\t",header=FALSE)
   names(dck.list)<-c("dck","description")
   data$dck<-as.numeric(data$dck)
   data$sid<-as.numeric(data$sid)

  if (is.na(sid.want)) {
    data2plot<- subset(data,dck==as.numeric(dck.want) & !is.na(data$report_timestamp))
  } else {
    data2plot<- subset(data,dck==as.numeric(dck.want) & sid==as.numeric(sid.want) & !is.na(data$report_timestamp))
  }

   cat("# reports",nrow(data2plot),"\n")
   if(print.comm)cat("subsetted data","\n")

   if ( dev != "screen" ) pdf(pdfname,width=8,height=11,paper='special')

   tmp<-def_layout()

   sdate<-as.Date(min(data2plot$report_timestamp))
   edate<-as.Date(max(data2plot$report_timestamp))

   ids.gen<-read.table("gen_id.txt")
   ids.gen<-as.vector(t(ids.gen))

   dck.title<-dck.list$description[which(dck.list$dck==as.numeric(dck.want))]
   dck.title<-as.character(dck.title)
   sid.title<-sid.list$description[which(sid.list$sid==as.numeric(sid.want))]
   sid.title<-as.character(sid.title)

   data2plot$longitude<-ifelse(data2plot$longitude >= 180, data2plot$longitude-360, data2plot$longitude)

   sdate2<-min(data2plot$report_timestamp,na.rm=T)
   edate2<-max(data2plot$report_timestamp,na.rm=T)

   # start constructing plot
   plot(0,type='n',axes=FALSE,ann=FALSE,xlim=c(0,1),ylim=c(0,1))
   # construct title and print as "margin text"
   if ( level == 0 ) {
     string <- sprintf("C3S2_D311_Lot1 Marine: ICOADS sid = %1.0f; dck = %1.0f", as.numeric(sid.want),as.numeric(dck.want))
   } else {  # level 2
     string <- sprintf("C3S2_D311_Lot1 Marine: ICOADS dck = %1.0f", as.numeric(dck.want))
   }
   if ( min(as.numeric(format(data2plot$report_timestamp,"%Y")),na.rm=T) >= 2015) string<-gsub("3.0.0","3.0.2",string)
   mtext(side=3,text = string,cex=1.5,adj=0.5)

   # construct header information and print in first window panel
   string <- sprintf("Date range = %s to %s",as.Date(sdate2),as.Date(edate2))
   text(0.0,0.8,labels = string,cex=1.1,adj=0)
   if ( level == 0 ) {
     string <- sprintf("Source = %s",sid.title)
   } else {  # level 2
     sid.title<-paste(unique(data2plot$sid),collapse="/")
     string <- sprintf("Contributing SID = %s",sid.title)
   }
   text(0.0,0.65,labels = string,cex=1.1,adj=0)
   string <- sprintf("Deck   = %s",dck.title)
   text(0.0,0.5,labels = string,cex=1.1,adj=0)
   string <- sprintf("Number of observations   = %1.0f",length(data2plot$dck))
   text(0.0,0.35,labels = string,cex=1.1,adj=0)

   if(print.comm)cat("text stuff","\n")

   # calculate number of observations in 1 deg lat/lon bins
   data2bin<-data2plot[,c("longitude","latitude")]
   data2bin$latitude[which(data2bin$latitude>=90.0)]<-89.999
   data2bin$longitude[which(data2bin$longitude>=180.0)]<-179.999
   xbin<-c(-180,180,1)
   ybin<-c(-90,90,1)
   nrep<-nrow(data2plot)

   x.bin <- seq(from=xbin[1],to=xbin[2],by=xbin[3])
   y.bin <- seq(from=ybin[1],to=ybin[2],by=ybin[3])

   if(print.comm)cat("bin prep","\n")

   freq1D<-bin.in.2d.buoy(data2bin,xbin = c(-180,180,1), ybin = c(-90,90,1))
   freq2D<-bin.in.2d(data2bin,xbin = c(-180,180,1), ybin = c(-90,90,1))
   n.ship<-sum(data2plot$pt %in% c(0,1,2,3,4,5) | is.na(data2plot$pt))
   n.moor<-sum(data2plot$pt == 6 | is.na(data2plot$pt))
   n.drift<-sum(data2plot$pt == 7 | is.na(data2plot$pt))
   n.cman<-sum(data2plot$dck %in% c(795,995))
   if ( nrep < 500 ) {
        # do x-y plot with red,circles
        #freq1D<-bin.in.2d.buoy(data2bin,xbin = c(-180,180,1), ybin = c(-90,90,1))
        plot(freq1D$X,freq1D$Y,pch=1,cex=1.1,yaxs='i', xaxs='i',col="red",
                xlim=range(x.bin),ylim=range(y.bin),axes=FALSE)
       if(print.comm)cat("bin lt 500","\n")
   } else if ( nrep <= n.moor | as.numeric(dck.want) %in% moor.dck ) {
        plot(freq1D$X,freq1D$Y,pch=1,cex=1.1,yaxs='i', xaxs='i',col="black",
                xlim=range(x.bin),ylim=range(y.bin),axes=FALSE)
   } else if ( nrep == n.cman | as.numeric(dck.want) %in% cman.dck ) {
        plot(freq1D$X,freq1D$Y,pch=1,cex=1.1,yaxs='i', xaxs='i',col="blue",
                xlim=range(x.bin),ylim=range(y.bin),axes=FALSE)
   #} else if ( length(data2plot$pt[which(data2plot$pt==6 )]) < nrep ) {
   } else {
	image(x.bin, y.bin, log(freq2D),axes=FALSE)
	# do normal shaded map
	#freq2D<-bin.in.2d(data2bin,xbin = c(-180,180,1), ybin = c(-90,90,1))
        #if(print.comm)cat("bin map","\n")
	# check for e.g. CMAN
	#if( length(table(freq2D)) > 360 ) {
	#image(x.bin, y.bin, log(freq2D),axes=FALSE)
	#} else if ( length(data2plot$pt[which(data2plot$pt>=6)]) > 0.5*nrep) {
        #freq1D<-bin.in.2d.buoy(data2bin,xbin = c(-180,180,1), ybin = c(-90,90,1))
        #plot(freq1D$X,freq1D$Y,pch=1,cex=1.1,yaxs='i', xaxs='i',col="blue",
        #        xlim=range(x.bin),ylim=range(y.bin),axes=FALSE)
	#} else {
	#image(x.bin, y.bin, log(freq2D),axes=FALSE)
	#}
   #} else {
#	# do x-y plot with circles
#	freq1D<-bin.in.2d.buoy(data2bin,xbin = c(-180,180,1), ybin = c(-90,90,1))
#	plot(freq1D$X,freq1D$Y,pch=1,cex=1.1,yaxs='i', xaxs='i',
#		xlim=range(x.bin),ylim=range(y.bin),axes=FALSE)
   }
   axis(side = 1, at = seq(-180,180,30),tcl=-.3,padj=-1)
   axis(side = 3, at = seq(-180,180,30),tcl=-.3,label=FALSE)
   axis(side = 4, at = seq(-90,90,15),tcl=-.3,label=FALSE)
   axis(side = 2, at = seq(-90,90,15),tcl=-.3,las=1,hadj=0.5)
   maps::map(database='world',add=TRUE,col="green",fill=FALSE,interior=FALSE)

   if(print.comm)cat("done map","\n")

   # histos of precision lat/lon
   extra<-seq(0,0.9,.1) # make sure we have all the columns

   tvar<-data2plot$latitude
   tvar<-c(tvar,extra)
   tvar<-round(tvar%%1,1)
   tmp_table<-table(round(tvar%%1,1))-1
   tmp_table<-round(tmp_table/nrep*100,1)
   yl<-range(tmp_table)
   yl[1]<-0
   yl[2]<-max(pretty(yl[2]*1.1))
   par(mar=c(1,1,1,0))
   barplot(tmp_table,col="white",axes=FALSE,names.arg="",ylim=yl)
   box()
   mtext("Lon. Prec.",side=2,line=1,adj=0,cex=0.6,padj=0)

   if(print.comm)cat("done lon prec","\n")

   tvar<-data2plot$longitude
   tvar<-c(tvar,extra)
   tvar<-round(tvar%%1,1)
   tmp_table<-table(round(tvar%%1,1))-1
   tmp_table<-round(tmp_table/nrep*100,1)
   yl<-range(tmp_table)
   yl[1]<-0
   yl[2]<-max(pretty(yl[2]*1.1))
   barplot(tmp_table,col="white",axes=FALSE,las=2,ylim=yl)
   box()
   mtext("Lat Prec.",side=2,line=1,adj=0,cex=0.6,padj=0)

   if(print.comm)cat("done lat prec","\n")

   extra<-seq(0,23,1)
   tvar<-floor(as.numeric(format(data2plot$report_timestamp,"%H")))
   tvar<-c(tvar,extra)
   tmp_table<-table(tvar)-1
   tmp_table<-data.frame(round(tmp_table/nrep*100,1))
   time_table<-tmp_table
   colnames(time_table)<-c("hour","UTC")

   if ( !("ltime" %in% names(data2plot) ) ) {
     if ( sum(!is.na(data2plot$report_timestamp)) > 0 ) {
       data2plot<-calc_local(data2plot)
       data2plot$ltime <-as.numeric(format.POSIXct(data2plot$local, "%H"))
       data2plot$local<-NULL
     } else {
       data2plot$ltime<-NA
     }
   }

   tvar<-data2plot$ltime
   tvar<-c(tvar,extra)
   tmp_table<-table(tvar)-1
   tmp_table<-data.frame(round(tmp_table/nrep*100,1))
   time_table<-cbind(time_table,tmp_table[[2]])
   colnames(time_table)[3]<-"local"

   yl<-range(time_table[,2])
   yl[1]<-0
   yl[2]<-max(pretty(yl[2]*1.1))
   barplot(time_table[,2],ylim=yl,col="white",las=2,axes=FALSE,names.arg="")
   mtext("Hour UTC",side=2,line=1,adj=0,cex=0.6,padj=0)

   if(print.comm)cat("done UTC","\n")

   yl<-range(time_table[,3])
   yl[1]<-0
   yl[2]<-max(pretty(yl[2]*1.1))
   bp<-barplot(time_table[,3],ylim=yl,col="white",las=2,axes=FALSE)
   subs<-seq(1,23,2)
   bp2<-bp[subs]
   axis(side=1,at=bp2,labels=seq(0,23,2),las=2,cex=0.8)
   mtext("Hour local",side=2,line=1,adj=0,cex=0.6,padj=0)

   if(print.comm)cat("done local","\n")

   # restore no margins
   par(mar=c(0,0,0,0))

   # Information on ID availability
   num.id.gen<-sum(data2plot$id %in% ids.gen)
   num.id.miss<-sum(data2plot$id.class=="missing")
   num.id.invalid<-sum(data2plot$id.class=="invalid")
   num.id.valid<-nrow(data2plot) - num.id.miss - num.id.invalid - num.id.gen

   plot(0,xlim=c(0,1),ylim=c(0,1),type='n',axes=FALSE,ann=FALSE)
   string <- sprintf("ID valid = %s ",num.id.valid)
   text(0.0,0.6,labels = string,cex=1.1,adj=0)
   string <- sprintf("ID invalid = %s ",num.id.invalid)
   text(0.0,0.35,labels = string,cex=1.1,adj=0)
   string <- sprintf("ID generic or missing = %s ",num.id.gen + num.id.miss)
   text(0.0,0.1,labels = string,cex=1.1,adj=0)

   wklen <- max(data2plot$report_timestamp,na.rm=T)-min(data2plot$report_timestamp,na.rm=T)
   units(wklen)<-"weeks"

   # toggle between days, months and years for histo
     if (wklen >= 52*30) {
   	h.int<-"years"
     } else if ( wklen >= 52*5 ) {
   	h.int<-"months"
     } else {
        h.int<-"weeks"
     }

   # consolidate ICOADS PT flag into 4 platform types
   data2plot$platform<-rep("Other",length(data2plot$pt))
   data2plot$platform[which(data2plot$pt>=0 & data2plot$pt<=5)] = "Ship"
   data2plot$platform[which(data2plot$pt==6 )] = "M.buoy"
   data2plot$platform[which(data2plot$pt==7 )] = "D.buoy"

   # get histogram counts to scale all histos by total obs
   h.tmp<-hist(data2plot$report_timestamp,breaks=h.int,plot=FALSE)
   yl<-range(pretty(h.tmp$counts))
   yl[1]<-0

   options(warn=-1)  # turn off warnings about histogram calls

   plat.list <- c("Ship","M.buoy","D.buoy","Other")

   for ( iplat in plat.list ) {

   if(print.comm)cat(iplat,"\n")

   xvals<-pretty(data2plot$report_timestamp,n=10)

   # subset data on platform type
   d.sub<-data2plot[which(data2plot$platform==iplat),]
   if ( iplat == plat.list[length(plat.list)]) {
   	# plot histogram of all data in pale colour, bottom plot
   	# (other) has x-axis label
           if(h.int=="years") {
             xvals.txt<-format(xvals,"%Y")
           } else if (wklen<4) {
             xvals.txt<-format(xvals,"%Y-%m-%d")
           } else {
             xvals.txt<-format(xvals,"%Y-%m")
           }
   	hist(data2plot$report_timestamp,breaks=h.int,xlab="",ylab="",cex.axis=1.2,
   	main="",xaxt='n',yaxt='n',col="white",border="wheat3",ylim=yl,freq=TRUE)
           axis(side=1,at=as.numeric(xvals),labels=xvals.txt,cex.axis=1.1)
   } else {
   	# without x-axis label
   	hist(data2plot$report_timestamp,breaks=h.int,xlab="",ylab="",
   	main="",xaxt='n',yaxt='n',col="white",border="wheat3",ylim=yl,freq=TRUE)
   }
   if (length(d.sub$pt>0 )) {
   	# and overplot data subset for each platform type
   	hist(d.sub$report_timestamp,breaks=h.int,xlab="",ylab="",
   	main="",xaxt='n',yaxt='n',add=TRUE,ylim=yl,freq=TRUE)
   }
   	# label platform name
   	mtext(side=2,text=iplat,las=2)
   }

   # by ECV

   ecv.list <- c("SLP","SST","AT","HUM","WS","WD")
   if ( !("HUM_observation_value") %in% names(data2plot) ) ecv.list<-gsub("HUM","DPT",ecv.list)

   if(print.comm)cat("about to do histos","\n")

   labs<-c("SLP","SST","AT","DPT","WS","WD")

   icount<-0
   for ( ev in ecv.list ) {
     icount<-icount+1
     ivar<-paste0(ev,"_observation_value")
     #ivar<-ev
     if(print.comm)cat(ivar,"\n")
     d.sub<-data2plot[which(data2plot[ivar]>-9999),]
     if ( ev == ecv.list[length(ecv.list)] ) {
   	h<-hist(data2plot$report_timestamp,breaks=h.int,xlab="",ylab="",cex.axis=1.2,
   	main="",xaxt='n',yaxt='n',col="white",border="wheat3",ylim=yl,freq=TRUE)
           axis(side=1,at=as.numeric(xvals),labels=xvals.txt,cex.axis=1.1)
     } else {
   	h<-hist(data2plot$report_timestamp,breaks=h.int,xlab="",ylab="",
   	main="",xaxt='n',yaxt='n',col="white",border="wheat3",ylim=yl,freq=TRUE)
     }
     mtext(side=2,text=labs[icount],las=2)
     if (nrow(d.sub)>1 ) {
   	h<-hist(d.sub$report_timestamp,breaks=h.int,xlab="",ylab="",
   	main="",xaxt='n',yaxt='n',add=TRUE,ylim=yl,freq=TRUE)
     }
   }

   options(warn=0)

   mtext("C3S2_D311_Lot1 marine data summary: input from ICOADS R3.0.0/2", side = 1, line = 3, outer = FALSE,font=3,col="grey")

   if ( dev != "screen" ) 	dev.off()

   if(print.comm)cat("done plot","\n")

   return(data2plot)
}
