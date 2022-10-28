#!/usr/bin/perl - w

#script to extract occurrences of definitions in a File
#output: definition candidates sorted by patterns
#usage: perl SentEx_patternsF.pl Korpus Patternlist



use utf8;
binmode STDIN, 'utf8';
binmode STDOUT, 'utf8';

$file = shift(@ARGV);
$pat = shift(@ARGV);
if ($file=~/\//){
($filestem) = $file=~ /.*\/(.+)\..../;
}
else {
($filestem) = $file=~ /(.+)\..../;
}

print STDERR "F:$filestem\n";

print STDERR "\n\nDo you want to evaluate against recall test set? If yes enter recall test set file else press return!\n";
# $recalltestset=<>;
$recalltestset="";
&recalltestset;


open(PAT, "<:utf8", "$pat") || die "Cannot open file:$!";
open(OUT, ">:utf8", "ALLPATTERNEVALUATION_$filestem"."\.txt") || die "Cannot open outfile:$!";

push @predefinedpatterns, "0"; #zato da se potem zacne z 1 ne 0
while (<PAT>){
chomp;
if (length>0){
  if (m/^\#/){}
else {
print STDERR "[$_]\n\n";
s/{{{(.*)}}}/$1/;
push @predefinedpatterns, "$1";

}
}
}
$k=$#predefinedpatterns;
for ($i=1;$i<=$k; $i++){
$count=0;
$yes=0;
$no=0;
$undef=0;
$allpozit=0;
$allneg=0;
$stop=0;
$eval=0;
@comments=();

print STDERR "PATLIST$i:". $predefinedpatterns[$i]."\n";

#open(OUT1, ">:utf8", "PAT_lema".$i."_$filestem."."xml") || die "Cannot open outfile1:$!";
open(OUT2, ">:utf8", "PAT_".$i."_$filestem."."txt") || die "Cannot open outfile2:$!";

open(FILE, "<:utf8", "$file") || die "Cannot open file:$!";
@positivesbyeachpattern=();

  $/ = "\/>\n";#"\n\n";#"<S/>";
  while (<FILE>) {  
    $s = $_;

      if ($s=~/defvalue=\"Y/){
	$allpozit++;
      }
      if ($s=~/defvalue=\"N/){
	$allneg++;
      }
    if ($s =~/.*?(<id_sp.*?\>).*?\n/){

($ids)= $s =~/.*?(<id_sp.*?\>).*?\n/g; 


}

$s =~s/.*?<id_sp.*?\>.*?\n//gs; 
($sentmeta)= $s =~ /(<S sid_sp.*)/;
#print STDERR "$sentmeta";
@wordforms = $s =~ /(.*?)\t.*?\n/gs;
    $string = join(" ", @wordforms);

    @lines = split(/\n/, $s);

    @msds = ();
   @token_type_msd = ();
    foreach $line (@lines) {

     if ($line =~ /((.*?\t+TOK\t)|(angl?\.?\t+TOK_ABBR\t))/){


  ($token,$type,$msd) = $line =~ /(.+?)\s*\t+.+\t+(.+?)\s*\t+(.+?)\s*\t*\s*$/;
#$msd=~s/(.*?)\s+/$1/;
$token_type_msd=$token."_____".$type."_____".$msd;
 #print STDERR $token_type_msd."\n";
#print "$token_type_msd"."\n";
          push (@token_type_msd, $token_type_msd);
          }
 

      
    } 
    $msd_string = join(" ", @token_type_msd); 
#print STDERR  $msd_string."]\n";
#  print $msd_string."\n\n\n";
#print "PAT$i:","$predefinedpatterns[$i]"."\n";
if ($msd_string =~ /$predefinedpatterns[$i]/){    #v resnici token type msd
#print STDERR  $msd_string."]\n\n";
#print STDERR "\nYES PREVIOUS MATCHED\n";
if ($stop==0){#da ga samo enkrat sprinta
print OUT2 "\n>>>>".$i.":\t"."{{{$predefinedpatterns[$i]}}}"."\n";
$stop=1;
}
      #print OUT1 "$s"."\n";
      print OUT2 "$string###$sentmeta"."\n";
$sentmeta=~/S sid_sp=\"(\d+)\"/;
$idnb=$1;
$union{$idnb}="$string###$sentmeta"."\n";
#print OUT2 "MSD string: $msd_string"."\n";
if ($sentmeta=~/defvalue=\"Y/){
$yes++;
$unionYES{$idnb}++;
push @positivesbyeachpattern, $idnb;

}
elsif ($sentmeta=~/defvalue=\"N/){
$no++;
$unionNO{$idnb}++;
}
else {
$undef++;
$unionUNDEF{$idnb}++;
}
$count++;

    }

}








$eval=$count-$undef;


if ($count==0) {
$count=0.000001;
push @comments, "\$undefWas0";
}
if ($allpozit==0) {
$allpozit=0.000001;
push @comments, "\$allpozitWas0";
}

if ($eval==0) {
###print OUT "EVAL IS ".$eval." and changed to=0.00001 \n";
$eval=0.00001;
###print OUT "nEWEVAL IS ".$eval.":::\n";
push @comments, "\$evalWas0";
}    

print OUT "PATTERN$i:\t{{{$predefinedpatterns[$i]}}}\n";
print OUT "TOTAL EXAMPLES: ".$count."\n";
print OUT "TOTAL EVALUATED: ".$eval."\n";
print OUT "POZITIVES:". $yes."\n";
print OUT "NEGATIVES:". $no."\n";
print OUT "UNDEFINED:". $undef."\n";
print OUT "ALLPOZ:".$allpozit."\n";
print OUT "ALLNEG:".$allneg."\n";
print OUT "PRECISION_eval:". $yes/$eval."\n";
#print OUT "PRECISION_noneval:". $yes/$count."\n";
#print OUT "RECALL:".$yes/$allpozit."\n";
#print OUT "POZ//UNDEF:\t"."$yes//".$undef."\n";
#print OUT "PREC//RECALL:".$yes/$eval."//".$yes/$allpozit;

#print OUT "POZITIVESBYPATTER>$i: "."@positivesbyeachpattern";

#presek  @recalltestsetids in @positivesbyeachpattern
  foreach $element (@positivesbyeachpattern,  @recalltestsetids) { $count{$element}++ }
    foreach $element (keys %count) {
	push @{ $count{$element} > 1 ? \@intersection : \@difference }, $element;
    }  
print OUT "INTERSECTION:"."number elements:[".@intersection."]:"."@intersection"."\n";
&computerecall;
print OUT "RECALL ON RECALL TEST SET:".@intersection."/". @recalltestsetids."=$divided\n";
print OUT "(recall test set is:$recalltestset)\n";


#print OUT "Ints reason : "."PozByPatt:"."@positivesbyeachpattern"."recallset"." @recalltestsetids"."\n";
#$ints=@intersection."\n";
#print STDERR "\n\nRECALL: $ints"."\\"."$number_recall"."\n";

#print OUT "WorstPrec (if all non eval were ng:".$yes/$count;
print OUT "\n\n======\n\n";
#print OUT "COMMENTS:"."@commetns";

%count=();
@intersection=();

}

open (OUTUNION, ">:utf8", "outunion.txt");
foreach $key (sort sortAsc keys %union){
print OUTUNION "$union{$key}";

}
@unionpositivesbyeachpattern= keys %unionYES;
  foreach $element (@unionpositivesbyeachpattern,  @recalltestsetids) { $count4union{$element}++ }
    foreach $element (keys %count4union) {
	push @{ $count4union{$element} > 1 ? \@intersection4union : \@difference4union }, $element;
    }  
&computerecall;

print OUT "\n\n\nALL PATTERNS, i.e. UNION\n";



print OUT "TOTAL EXAMPLES in UNION: ";
print OUT scalar  keys %union; $scalarall= scalar keys %union;
print OUT "\n";
print OUT "POZITIVES:";
print OUT scalar keys %unionYES; $scalaryes= scalar keys %unionYES;
print OUT "\n";
print OUT "NEGATIVES:";
print OUT scalar keys %unionNO;
print OUT "\n";
print OUT "UNDEFINED:";
print OUT scalar keys %unionUNDEF; $scalarundefined= scalar keys %unionUNDEF;
print OUT "\n";
$scalardefined=$scalarall-$scalarundefined;
# print OUT "PRECISION_eval:". $scalaryes/ $scalardefined."\n";
print OUT "INTERSECTION:"."number elements4union:[".@intersection4union."]:"."@intersection4union"."\n";
  if ($chosenrecall>0){
$iu=@intersection4union;
$rt=@recalltestsetids;
$dividedunion=$iu/$rt;
print OUT "RECALL ON RECALL TEST SET:".@intersection4union."/". @recalltestsetids."=$dividedunion\n";
print OUT "(recall test set is:$recalltestset)\n";
}

  sub sortAsc {

           $a<=>$b;
         }

sub recalltestset {
print STDERR "you entered:[".$recalltestset."]\n";
# chomp $recalltestset;
$recalltestset=~s/\n*\r*$//g;
print STDERR "CHOMPED:: [".$recalltestset."]\n";

if ($recalltestset=~/.../){
$chosenrecall=1;
open(RCSET, "<:utf8", "$recalltestset") || die "Cannot open RCSET file:$!";
while (<RCSET>){
  if (m/S sid_sp=\"(\d+)\"/){
push @recalltestsetids, $1;
}
}

}
else {print STDERR "\nok no test set for recall!\n";}

}

sub computerecall {
  if ($chosenrecall>0){
$is=@intersection;
$rs=@recalltestsetids;
$divided=$is/$rs;
}
}

print STDERR "total number of recall testset:  ".@recalltestsetids."\n";
