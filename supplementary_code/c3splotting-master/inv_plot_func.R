
#--------------------------------------------------------------------------------
Sys.setenv(TZ='GMT')
#--------------------------------------------------------------------------------

is.leapyear=function(year){
  #http://en.wikipedia.org/wiki/Leap_year
  return(((year %% 4 == 0) & (year %% 100 != 0)) | (year %% 400 == 0))
}

add_date2 <- function(df){
# adds date variable to file based on yr, mo, dy, hr, invalid set to missing
# also generates date variable with missing hour set to local noon
# adds date.flag
# 0 = valid date & time
# 1 = invalid date or time (time not missing)
# 2 = valid date, hr missing, 12 local added

#------------------------------------------------------------------------------------------------------
# add date variable
#------------------------------------------------------------------------------------------------------
#print('about to add date')
  df$date.flag <- 0
  # need to catch and remove any data with invalid dates (e.g. 31 June)
  df$dy[which(df$mo %in% c(4,6,9,11) & df$dy==31)] <- NA
  df$dy[which(df$mo==2 & df$dy>29)] <- NA
  df$dy[!is.leapyear(df$yr) & df$mo==2 & df$dy==29] <- NA
  df$date.flag<-ifelse(is.na(df$dy), 1, df$date.flag)

#------------------------------------------------------------------------------------------------------
# put missing hour to midday local
#------------------------------------------------------------------------------------------------------
  time_string <- ifelse(df$date.flag!=1,sprintf("%4d-%02d-%02d 12:00", df$yr, df$mo, df$dy ),NA)
  my_date_time <- as.POSIXct(time_string) + (df$lon / 15)*3600
  local_noon <- round(as.numeric(format.POSIXct( my_date_time ,"%H")) + as.numeric(format.POSIXct( my_date_time ,"%M"))/60,0)
  local_noon <- ifelse(local_noon > 23, local_noon-24, local_noon)

  df$date.flag<-ifelse(is.na(df$hr) & !is.na(df$dy), 2, df$date.flag)
  tmphr <- ifelse(is.na(df$hr) & !is.na(df$dy), local_noon, df$hr)

  tmp<- strftime(as.POSIXct(tmphr * 60 * 60, origin = "0001-01-01", tz = "GMT"), format = "%H:%M:%S")
#------------------------------------------------------------------------------------------------------
# add date
#------------------------------------------------------------------------------------------------------
  dd<-paste0(df$yr,"-",df$mo,"-",df$dy," ",tmp)
  dd[grepl("NA",dd)] <- NA
  df$date <- as.POSIXct(dd)
  #df$date <- ifelse ( df$date.flag %in% c(0,2), as.POSIXct(paste0(df$yr,"-",df$mo,"-",df$dy," ",tmp)), NA)
  #df$date <- ifelse ( df$date.flag %in% c(0,2), as.POSIXct(dd), NA)

return(df)
}

#------------------------------------------------------------------------------------------------------

def_layout <- function() {

  # define window setup

  # reference to higher panel numbers leaves them blank to give space
  # 1x full width (title goes in margin)
        m <- matrix(c(1,1,1),ncol = 3,byrow = TRUE)
  # left covers 5 rows
        mmax <- max(m)
        m <- rbind(m,matrix(c(mmax+1,-1,mmax+2,
                        mmax+1,-1,mmax+3,
                        mmax+1,-1,mmax+4,
                        mmax+1,-1,mmax+5,
                        mmax+1,-1,mmax+6),
                ncol = 3,byrow = TRUE))
  # 1 blank row
        m <- rbind(m,matrix(c(-1,-1,-1),ncol = 3,byrow = TRUE))
  # 4 full width rows for plat histos
        for (i in 1:4) {
        mmax <- max(m)
        m <- rbind(m,matrix(c(mmax+1,mmax+1,mmax+1),ncol = 3,byrow = TRUE))
        }
  # 1 blank row
        m <- rbind(m,matrix(c(-1,-1,-1),ncol = 3,byrow = TRUE))
  # 8 full width rows for plat histos
        for (i in 1:8) {
                mmax <- max(m)
                m <- rbind(m,matrix(c(mmax+1,mmax+1,mmax+1),ncol = 3,byrow = TRUE))
        }
  mmax <- max(m)
  m[which(m[,3]<0),3]<-mmax+1
  m[which(m[,2]<0),2]<-mmax+1
  m[which(m[,1]<0),1]<-mmax+1
  #layout.show(mmax)

  par(mar = c(0.0,0.0,0.0,0.0), oma =c(4,4,4,4))
  tmp.ht<-rep(1,times=dim(m)[1])
  tmp.ht[1]<-2.5  # title box
  tmp.ht[2:6]<-1.5  # map & 5 plots to the side
  layout(m,widths=c(7,0.5,3),heights=tmp.ht) # slim panel for spacing

  return()
}

#---------------------------------------------------------------------------------

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

#---------------------------------------------------------------------------------

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

#---------------------------------------------------------------------------------

#' Local Time Calculation
#'
#' @param df must contain longitude and date
#'
#' @return Adds local time and a flag to input data frame
#' @export
#'
#' @examples
calc_local<-function(df) {

  if (!("lat" %in% names(df) ) ) df$lat<-df$latitude
  if (!("lon" %in% names(df) ) ) df$lon<-df$longitude
  if (!("date" %in% names(df) ) ) df<-add_date2(df)

  loc.dck<-c(150,151,152,154,155,156,192,193,194,197,201,202,203,204,215,246,247,254,281,667,701,702,711,720,721,730,734,736,761,762,901)

  df$lon<-ifelse(df$lon >= 180,df$lon-360,df$lon) ## tc 09 aug 2021

  #offs<-round((df$lon+7.5)/15)*60*60
  offs<-round((df$lon)/15)*60*60
  df$local<-df$date+offs

  ttl<-table(df$dck,format(df$local,"%H"))
  ttl<-ttl/rowSums(ttl)
  ttl[which(ttl<0.01)]<-0
  ttg<-table(df$dck,format(df$date,"%H"))
  ttg<-ttg/rowSums(ttg)
  ttg[which(ttg<0.01)]<-0

  nl<-rowSums(ttl>0)
  ng<-rowSums(ttg>0)

  loc.dck<-rownames(ttl)[nl<ng]
  loc.dck<-loc.dck[!(loc.dck %in% c(732))]
  gmt.dck<-rownames(ttg)[nl>ng]
  if("732" %in% unique(df$dck)) gmt.dck<-sort(unique(c(732,gmt.dck)))
  unk.dck<-rownames(ttg)[nl==ng & nl != 24]
  unk.dck<-unk.dck[!(unk.dck %in% c(732))]
  hrl.dck<-rownames(ttg)[nl==ng & nl == 24]
  hrl.dck<-hrl.dck[!(hrl.dck %in% c(732))]

  df$lhr<-as.numeric(format(df$local,"%H"))

  tt<-table(df$dck,df$lhr%%4)
  tt0<-round(tt[,1]/rowSums(tt),2)

  offs2<-df$lhr%%4
  offs2<-ifelse(offs2==3,-1,offs2)
  adj.dck<-unique(c(names(tt0)[tt0>0.75],seq(150,156),193,201,202,203,204,215,762))
  if(df$yr[1] < 1920 ) adj.dck<-c(adj.dck,c(254))
  gmt.dck<-gmt.dck[!(gmt.dck %in% adj.dck)]
  unk.dck<-unk.dck[!(unk.dck %in% adj.dck)]
  hrl.dck<-hrl.dck[!(hrl.dck %in% adj.dck)]
  df$local<-ifelse(df$dck %in% adj.dck,df$local-offs2*60*60,df$local)
  df$local<-as.POSIXct(df$local,origin=as.Date("1970-01-01"))

  #print(table(df$dck,format(df$local,"%H")))
  #df$local[!(df$dck %in% loc.dck)]<-NA
  df$lhr<-NULL
  #print(table(format(df$local,"%H"),df$dck))
  df$samp.flag<-"A"
  df$samp.flag<-ifelse(df$dck %in% loc.dck | df$dck %in% adj.dck,"L",df$samp.flag)
  df$samp.flag<-ifelse(df$dck %in% gmt.dck,"U",df$samp.flag)
  df$samp.flag<-ifelse(df$dck %in% hrl.dck,"H",df$samp.flag)

  return(df)

}

get_id_class2 <- function (dck, id, config) {
#get_id_class <- function (dck, id) {
    patterns <- jsonlite::fromJSON(paste0(config$json_files_path,
        "/dck", dck, ".json"))
    id_class <- rep("invalid", length(id))
    for (i in 1:length(patterns$patterns)) {
        ind <- grep(patterns$patterns[i], id)
        id_class[ind] <- names(patterns$patterns)[i]
    }
    id_class <- ifelse(dck == 849 & nchar(id) == 4, "callsign",
        id_class)
    id_class <- ifelse(id == "SHIP", "SHIP", id_class)
    id_class <- ifelse(id == "MASKSTID", "MASKSTID", id_class)
    id_class <- ifelse(id == "AAAA", "invalid", id_class)
    id_class <- ifelse(nchar(id) == 0, "missing", id_class)
    id_class <- ifelse(is.na(id), "missing", id_class)
    id_class <- ifelse(dck==700 & grepl("^[0-9]{5}$",id), "buoy_number", id_class)

    #if(sum(id_class=="invalid") > 0 ) {
    #  print(table(id[id_class=="invalid"]))
    #}
    return(id_class)
}
