---
title: 'Thinking Functionally About The Actor Model'
date: 2023-12-09
summary: "Think about the actor model not in a procedural way, but in a functional way. Maybe it could be a 'hactor' model!"
draft: false
---

## Thinking Functionally

If you read the previous post about [The Actor Model in a C# World][actormodeldotnet], I was thinking of how the Actor Model influenced me towards thinking more functionally and also going down the path of teaching myself [Haskell][learnyouahaskell]. 

If I had a file and wanted to count unique word counts using Haskell, how would that look?

```haskell
module Main where

import System.IO  
import Data.List
import qualified Data.Map as M
import qualified Data.Map.Strict as MS

main :: IO ()
main = do
    withFile "/home/david/code/git/actorfunc/app/doc.txt" ReadMode (\handle -> do
        contents <- hGetContents handle 
        let textContents = contents
        putStrLn $ show $ countWordsInDoc textContents)

--- Take the top 10 words from a sorted list
countWordsInDoc :: String -> [(String, Int)]
countWordsInDoc contents = take 10 $ sortedList
    --- lines contents breaks the file into an array of Strings
    --- countLines takes an empty Map and the array of String
    --- the return of countLines is then sorted, in descending order of the value (the count)
    where sortedList = sortBy (\(k1, v1) (k2, v2) -> v2 `compare` v1) $ M.toList $ countLines M.empty $ lines contents

countLines :: (M.Map String Int) -> [String] -> (M.Map String Int)
--- if the array of lines is empty, return the Map (exit case of recursion)
countLines map [] = map
--- if we have lines to process, then take our existing Map and union it with wordMap's result
countLines map (l:ls) = countLines (M.unionWith (+) map wordMap) ls
    --- call countWords after breaking the current line into an array of strings
    where wordMap = countWords M.empty $ words l


countWords :: (M.Map String Int) -> [String] -> (M.Map String Int)
--- if we're all out of words (empty list) then return the map (exit recursion case)
countWords map [] = map
--- if we have words to process, then use a nifty insertWith function to increment our Map
---  if the value in the Map exists, increment the value by 1; otherwise, set the value to 1
countWords map (w:ws) = countWords (MS.insertWith (+) w 1 map) ws
```

What's happening here? Quite a bit and it's pretty slick how little code has to be written in order to accomplish so much.

The comments in the code above describe what's going on, and it generally helps to work from the bottom up in reading functional code (at least that's how my brain functions).

Now, compared to the Actor Model example, there's a lot of limitations here. There's no scaling going on here, no concurrency. Everything happens sequentially. But you can kind of see how the Actor Model tends to lend itself to thinking of problems more functionally. When you break a problem down into functions and messages (what needs to be passed where and when), things start to come together.

Hope you enjoyed this little aside.



[learnyouahaskell]: http://learnyouahaskell.com/
[actormodeldotnet]: /assets/images/blog/actor-model-dotnet