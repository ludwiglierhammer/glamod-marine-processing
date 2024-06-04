my_args = commandArgs(trailingOnly=TRUE)

# if running on command line, the above code sets my_args
# to the command line arguments. If running within an
# R or Rstudio session, need to set my_args2 to the
# wanted values which are then used if no command line input

if (length(my_args) == 0) my_args<-my_args2

# if a single input deck, run 100 dck, else 2nd value is end dck
start.dck<-as.numeric(my_args[1])
if(length(my_args) == 2 ) {
  end.dck<-as.numeric(my_args[2])
} else {
  end.dck<-start.dck+99
}

# config file sets input and output directories
config<-config::get(file = "./config_level2.yml")

source("read_level2.R")
source("inv_plot.R")
source("dck_sid_summary.R")

# loop over dck
for ( dck.want in as.character(seq(start.dck,end.dck,1)) ) {

  cat("checking dck", dck.want, "\n")

  got.files<-0

  # see which sid are present
  for ( sid in as.character(seq(1,299,1)) ) {
    df<-NULL
    sid.want<-paste0("00",sid)
    sid.want<-substring(sid.want,nchar(sid.want)-2,nchar(sid.want))
    #if (is.null(df) ) next
    # this generates the temporary output files, per sid
    #outfile<-paste0("/work/scratch-nopw/eckent01/level2/",dck.want,"_",sid.want,".Rda")
    if (!dir.exists(config$output_path_data) ) dir.create(config$output_path_data,recursive=TRUE)
    outfile<-paste0(config$output_path_data,dck.want,"_",sid.want,".Rda")
    df<-lev2(dck.want,sid.want)
    if (is.null(df) ) next
    got.files<-got.files+1
    cat("writing",outfile,"\n")
    saveRDS(df,outfile)
  }

  # skip to next dck if no files found
  if(got.files==0) next

  # list of files to read in, maybe several sid for single dck
  flist<-list.files("/work/scratch-nopw/eckent01/level2",patt=paste0(dck.want,"_"),full.names=T)
  if ( length(flist) == 0 ) next
  df<-do.call(rbind,lapply(flist,readRDS))
  df<-df[df$yr<=2021,]  # got partial data for 2022, not using for R5

  if ( !dir.exists(config$output_path_pdf) ) dir.create(config$output_path_pdf, recursive=TRUE)
  pdfname<-paste(config$output_path_pdf,'C3S2_D311_Lot1_Marine_dck',dck.want,'.pdf',sep="")
  p<-inv_plot(level=2,data=df,dck.want=dck.want,sid.want=NA,dev="pdf",pdfname=pdfname)

  # inventory summary per dck/sid so split
  sp<-split(df,df$sid)
  for (sid.want in names(sp) ) {
     df<-sp[[sid.want]]
     op<-dck_sid_summary(df,sid_txt_file="sid_list.txt",dck_txt_file="dck_list.txt",inv.ver="2")
     if ( !dir.exists(config$output_path_txt) ) dir.create(config$output_path_txt, recursive=TRUE)
     write.table(op,paste0(config$output_path_txt,"",dck.want,"_",sid.want,".txt"),sep=",",col.names=T)
  }

}
