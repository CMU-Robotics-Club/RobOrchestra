public class ComparableIntArr implements Comparable<ComparableIntArr>
{
  public int[] value;
  public ComparableIntArr(int[] arr)
  {
    value = arr;
  }
  
  public boolean equals(Object o){
    if(o.getClass() != this.getClass()) return false;
    return this.compareTo((ComparableIntArr)o)==0;
  }
  public int compareTo(ComparableIntArr other)
  {
    int idx = 0;
    while (true)
    {
      if (value.length == idx && other.value.length == idx)
      {
        return 0;
      }
      else if (value.length == idx)
      {
         return -1;
      }
      else if (other.value.length == idx)
      {
        return 1;
      }
      else if (value[idx] < other.value[idx])
      {  
        return -1;
      }
      else if (value[idx] > other.value[idx])
      {
        return 1;
      }
      else
      {
        assert(value[idx] == other.value[idx]);
        idx++;
      }
    }
  }
}
