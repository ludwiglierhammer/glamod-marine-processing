

config<-config::get(file = "./config_level2.yml")

patt.want<-"^[0-9]{3}-[0-9]{3}$"
dirs<-c(list.files(config$release4_path,patt=patt.want,full.names=T),list.files(config$release5_path,patt=patt.want,full.names=T))

check.dir<-config$output_path_data

d1<-substr(basename(dirs),1,3)
d2<-substr(basename(dirs),5,7)
dirs<-sort(paste0(dirname(dirs),"/",d2,"_",d1))

icount<-0
icount0<-0
icount2<-0

for ( dir in dirs ) {
  fn<-paste0(check.dir,basename(dir),".Rda")
  lenf<-length(list.files(dir))

  #fn<-gsub("-","_",fn)
  if (file.exists(fn)) {
    cat("got",fn,"\n")
    icount<-icount+1
  } else if (lenf ==0) {
    cat("zero files",dir,"\n")
    icount0<-icount0+1
  } else {
    cat("missing",fn,"\n")
    icount2<-icount2+1
    stop()
  }
}
cat("# done",icount,"\n")
cat("# zero length",icount0,"\n")
cat("# not done",icount2,"\n")
